const { exec } = require('child_process');
const http = require('http');

let electronStarted = false;

function checkServer(tries = 0) {
    http.get('http://localhost:5000', (res) => {
        if (res.statusCode === 200 && !electronStarted) {
            startElectron();
        } else if (tries < 30) {
            setTimeout(() => checkServer(tries + 1), 1000);
        } else if (!electronStarted) {
            console.error('Server did not start in time');
        }
    }).on('error', (err) => {
        if (tries < 30) {
            setTimeout(() => checkServer(tries + 1), 1000);
        } else if (!electronStarted) {
            console.error('Server did not start in time', err);
        }
    });
}

function startElectron() {
    electronStarted = true;
    exec('electron .', (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            return;
        }
        console.log(`stdout: ${stdout}`);
        console.error(`stderr: ${stderr}`);
    });
}

// Start checking the server and the Electron app immediately
checkServer();
startElectron();