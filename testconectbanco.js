require('dotenv').config(); // Carregar variáveis de ambiente
const Firebird = require('node-firebird');

const options = {
  host: process.env.FIREBIRD_HOST,
  port: parseInt(process.env.FIREBIRD_PORT, 10),
  database: process.env.FIREBIRD_DB_PATH,
  user: process.env.FIREBIRD_USER,
  password: process.env.FIREBIRD_PASS,
  lowercase_keys: false,
  role: null,
  pageSize: 4096,
};

Firebird.attach(options, function (err, db) {
  if (err) {
    return console.error('❌ Erro na conexão:', err);
  }

  const query = 'SELECT FIRST 5 * FROM custom_listagem_de_itens';

  db.query(query, function (err, result) {
    if (err) {
      console.error('❌ Erro na consulta:', err);
    } else {
      console.log('📊 Resultado da view:');
      console.table(result);
    }

    db.detach();
  });
});
