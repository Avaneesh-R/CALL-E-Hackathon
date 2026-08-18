/**
 * Baileys WhatsApp REST server
 * Scan QR once → then POST /send to send messages from Python
 * Runs on http://localhost:3001
 */
const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const qrcode  = require('qrcode-terminal');
const http    = require('http');
const path    = require('path');

const PORT     = 3001;
const AUTH_DIR = path.join(__dirname, 'wa_auth');

let sock = null;
let ready = false;

async function connect() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        auth: state,
        printQRInTerminal: false,
        logger: require('pino')({ level: 'silent' }),
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n\nScan this QR code with WhatsApp (Settings > Linked Devices > Link a Device):\n');
            qrcode.generate(qr, { small: true });
            console.log('\nWaiting for scan...\n');
        }

        if (connection === 'open') {
            ready = true;
            console.log('✓ WhatsApp connected! Server ready on http://localhost:' + PORT);
        }

        if (connection === 'close') {
            ready = false;
            const code = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = code !== DisconnectReason.loggedOut;
            console.log('Connection closed. Reconnect:', shouldReconnect);
            if (shouldReconnect) {
                setTimeout(connect, 3000);
            } else {
                console.log('Logged out. Delete wa_auth/ and restart to re-scan.');
            }
        }
    });
}

// Format phone number to WhatsApp JID
function toJid(phone) {
    let digits = phone.replace(/\D/g, '');
    if (digits.startsWith('0')) digits = '91' + digits.slice(1);
    if (digits.length === 10) digits = '91' + digits;
    return digits + '@s.whatsapp.net';
}

// HTTP server
const server = http.createServer(async (req, res) => {
    res.setHeader('Content-Type', 'application/json');

    if (req.method === 'GET' && req.url === '/status') {
        res.end(JSON.stringify({ ready, status: ready ? 'connected' : 'waiting_for_qr' }));
        return;
    }

    if (req.method === 'POST' && req.url === '/send') {
        if (!ready) {
            res.statusCode = 503;
            res.end(JSON.stringify({ ok: false, error: 'WhatsApp not connected yet — scan QR first' }));
            return;
        }
        let body = '';
        req.on('data', d => body += d);
        req.on('end', async () => {
            try {
                const { phone, message } = JSON.parse(body);
                if (!phone || !message) throw new Error('phone and message required');
                const jid = toJid(phone);
                await sock.sendMessage(jid, { text: message });
                console.log(`  ✓ Sent to ${phone}: ${message.slice(0, 60)}`);
                res.end(JSON.stringify({ ok: true, jid }));
            } catch (e) {
                res.statusCode = 500;
                res.end(JSON.stringify({ ok: false, error: e.message }));
            }
        });
        return;
    }

    res.statusCode = 404;
    res.end(JSON.stringify({ error: 'not found' }));
});

server.listen(PORT, '127.0.0.1', () => {
    console.log(`WhatsApp server starting on port ${PORT}...`);
    connect();
});
