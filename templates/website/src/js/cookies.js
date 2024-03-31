function getClientId() {
  let match = document.cookie.match('(?:^|;)\\s*_ga=([^;]*)'),
    raw = match ? decodeURIComponent(match[1]) : null;
  if (raw) {
    match = raw.match(/(\d+\.\d+)$/);
  }
  return (match) ? match[1] : null;
}

function getCookieValue(name) {
  const regex = new RegExp(`(^| )${name}=([^;]+)`);
  const match = document.cookie.match(regex);
  if (match) {
    return match[2]
  }
}

function getAppendString() {
  let cookieData = getCookieValue('aatd');
  let appendString = "";
  const client_id = getClientId();
  if (cookieData) {
    appendString = decodeURIComponent(cookieData) + "&client_id=" + client_id;
  }
  else {
    appendString = "?client_id=" + client_id;
  }
  return appendString;
}

const url = location.href;
const regex = /\?/;
if (url.match(regex)) {
  const urlData = url.split("?");
  let trackingData = urlData[1].split("&");
  let cookieData = null;
  for (parameter = 0;parameter<trackingData.length;parameter++) {
    if (trackingData[parameter].startsWith("utm_") || trackingData[parameter].startsWith("client_id")){
      if (!cookieData){
        cookieData = "?" + trackingData[parameter];
      }
      else {
        cookieData = cookieData + "&" + trackingData[parameter];
      }
    }
  }
  if (cookieData) {
    document.cookie = "aatd=" + encodeURIComponent(cookieData)+ ";max-age=2629800";
  }
}
