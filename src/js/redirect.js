function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function slowRedirect() {
  await sleep(5000);
  window.location.replace('/')
}

slowRedirect();
