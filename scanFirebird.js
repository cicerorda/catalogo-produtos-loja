const net = require('net');
const baseIP = '192.168.0.'; // altere se a rede for diferente
const porta = 3050;
const timeout = 300;

console.log("🚀 Iniciando conexão...");

async function main() {
  // sua lógica aqui
  
function testarConexao(ip) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(timeout);

    socket.on('connect', () => {
      socket.destroy();
      resolve(ip);
    });

    socket.on('timeout', () => {
      socket.destroy();
      resolve(null);
    });

    socket.on('error', () => {
      resolve(null);
    });

    socket.connect(porta, ip);
  });
}

async function escanear() {
  console.log(`🔍 Escaneando IPs na faixa ${baseIP}1-254...`);
  const promessas = [];

  for (let i = 1; i <= 254; i++) {
    promessas.push(testarConexao(`${baseIP}${i}`));
  }

  const resultados = await Promise.all(promessas);
  const encontrados = resultados.filter(Boolean);

  if (encontrados.length) {
    console.log('✅ Servidores Firebird encontrados:');
    encontrados.forEach((ip) => console.log(` - ${ip}`));
  } else {
    console.log('❌ Nenhum servidor Firebird encontrado nessa faixa.');
  }
}

escanear();

  console.log("📦 Conexão e consulta feitas com sucesso.");
}

main().catch((err) => {
  console.error("❌ Erro geral:", err);
});

