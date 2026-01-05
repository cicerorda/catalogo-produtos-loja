const net = require('net');

const host = '192.168.0.98';
const port = 3050;

console.log(`🔌 Testando conexão com ${host}:${port}...`);

const socket = new net.Socket();
socket.setTimeout(3000);

socket.on('connect', () => {
  console.log(`✅ Conexão bem-sucedida com ${host}:${port}`);
  socket.destroy();
});

socket.on('timeout', () => {
  console.log(`⏳ Timeout - Porta ${port} pode estar bloqueada ou serviço desligado.`);
  socket.destroy();
});

socket.on('error', (err) => {
  console.log(`❌ Erro na conexão: ${err.message}`);
});

socket.connect(port, host);
