const cron = require('node-cron');
const { exec } = require('child_process');
const path = require('path');

// Agendar execução às 2h da manhã
cron.schedule('0 2 * * *', () => {
  console.log('⏰ Executando upload_recent_to_imagekit.py às 2h...');

  const scriptPath = path.join(__dirname, 'upload_recent_to_imagekit.py');
  exec(`python ${scriptPath}`, (error, stdout, stderr) => {
    if (error) {
      console.error(`❌ Erro ao rodar script: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`⚠️ STDERR: ${stderr}`);
      return;
    }
    console.log(`✅ Script executado com sucesso:\n${stdout}`);
  });
});
