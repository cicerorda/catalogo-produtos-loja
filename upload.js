const ImageKit = require("imagekit");
const fs = require("fs");
const path = require("path");
const os = require("os");



const pastaImagens = "./imagens";
const maxConcorrentes = 10;

fs.readdir(pastaImagens, async (err, arquivos) => {
  if (err) {
    console.error("❌ Erro ao ler a pasta:", err);
    return;
  }

  const fila = [...arquivos];
  const uploaders = [];

  for (let i = 0; i < maxConcorrentes; i++) {
    uploaders.push(processarUploads(fila));
  }

  await Promise.all(uploaders);
  console.log("✅ Todos os uploads finalizados.");
});

async function processarUploads(fila) {
  while (fila.length > 0) {
    const nomeArquivo = fila.shift();
    const caminho = path.join(pastaImagens, nomeArquivo);

    try {
      const result = await imagekit.upload({
        file: fs.readFileSync(caminho),
        fileName: nomeArquivo,
        folder: "/imagens"
      });

      console.log(`✅ Enviado: ${nomeArquivo} → ${result.url}`);
    } catch (error) {
      console.error(`❌ Erro ao enviar ${nomeArquivo}: ${error.message}`);
    }
  }
}