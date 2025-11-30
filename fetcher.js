// Basit IMAP fetcher + RabbitMQ producer (tek seferlik çalışır; production için loop/IDLE ekle)
require('dotenv').config();
const imaps = require('imap-simple');
const { simpleParser } = require('mailparser');
const amqplib = require('amqplib');

const RABBIT_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672';
const QUEUE_NAME = process.env.QUEUE_NAME || 'new_message';

async function pushToQueue(msg) {
  const conn = await amqplib.connect(RABBIT_URL);
  const ch = await conn.createChannel();
  await ch.assertQueue(QUEUE_NAME, { durable: true });
  ch.sendToQueue(QUEUE_NAME, Buffer.from(JSON.stringify(msg)), { persistent: true });
  await ch.close();
  await conn.close();
}

async function syncImap() {
  const config = {
    imap: {
      user: process.env.MAIL_USER,
      password: process.env.MAIL_PASS,
      host: process.env.MAIL_HOST || 'imap.gmail.com',
      port: parseInt(process.env.MAIL_PORT || '993'),
      tls: true,
      authTimeout: 3000
    }
  };

  const connection = await imaps.connect(config);
  await connection.openBox('INBOX');

  const searchCriteria = ['UNSEEN'];
  const fetchOptions = { bodies: [''], struct: true };

  const messages = await connection.search(searchCriteria, fetchOptions);
  for (const item of messages) {
    const part = item.parts.find(p => p.which === '');
    const raw = part ? part.body : null;
    if (!raw) continue;
    const parsed = await simpleParser(raw);

    const msg = {
      account: process.env.MAIL_USER,
      messageId: parsed.messageId || `${Date.now()}-${Math.random()}`,
      from: parsed.from ? parsed.from.value : [],
      to: parsed.to ? parsed.to.value : [],
      subject: parsed.subject || '',
      text: parsed.text || '',
      html: parsed.html || '',
      date: parsed.date || new Date().toISOString(),
      raw: raw, // raw e-mail (DKIM doğrulama için)
      attachments: (parsed.attachments || []).map(a => ({
        filename: a.filename,
        contentType: a.contentType,
        size: a.size,
        content: a.content.toString('base64') // base64 ile kuyruğa koy (küçük demo için)
      }))
    };

    await pushToQueue(msg);
    // mark as seen
    connection.addFlags(item.attributes.uid, '\\Seen', (err) => { if (err) console.error('Mark seen err', err); });
    console.log('Queued:', msg.subject);
  }

  connection.end();
}

(async () => {
  try {
    await syncImap();
    console.log('IMAP sync completed.');
    process.exit(0);
  } catch (err) {
    console.error('IMAP error', err);
    process.exit(1);
  }
})();
