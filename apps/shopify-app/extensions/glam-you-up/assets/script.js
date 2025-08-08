function errorToast(message) {
  let body = document.querySelector("body");
  let toast = document.createElement("p");
  toast.innerHTML = `<span style="font-weight: 700">Error!</span> ${message}`;
  toast.style.cssText =
    "padding: 5px 25px; background-color: #f1807e; color: white; position: fixed; z-index: 999; right: 20px;";
  body.appendChild(toast);
  setTimeout(function () {
    body.removeChild(toast);
  }, 10000);
}

function successToast(message) {
  let body = document.querySelector("body");
  let toast = document.createElement("p");
  toast.innerHTML = `<span style="font-weight: 700">Success!</span> ${message}`;
  toast.style.cssText =
    "padding: 5px 25px; background-color: #7ef180; color: white; position: fixed; z-index: 999; right: 20px;";
  body.appendChild(toast);
  setTimeout(function () {
    body.removeChild(toast);
  }, 10000);
}

function warningToast(message) {
  let body = document.querySelector("body");
  let toast = document.createElement("p");
  toast.innerHTML = `<span style="font-weight: 700">Warning!</span> ${message}`;
  toast.style.cssText =
    "padding: 5px 25px; background-color: #FFA500 ; color: white; position: fixed; z-index: 999; right: 20px;";
  body.appendChild(toast);
  setTimeout(function () {
    body.removeChild(toast);
  }, 10000);
}

function startProgress(time, parentNode = "body") {
  let body = document.querySelector(parentNode);
  let progressBarBack = document.createElement("div");
  progressBarBack.className = "loader-progress-bar-back";
  progressBarBack.id = "customProgressBar";
  if (parentNode == "body") {
    progressBarBack.style.width = "100%";
  } else {
    progressBarBack.style.width = "600px";
    progressBarBack.style.right = "0";
  }
  progressBarBack.innerHTML = `
      <div class="loader-progress-bar">
          <div class="loader-progress" style="width: 0%"> </div>
      </div>`;
  body.appendChild(progressBarBack);
  onProgress(time);
}

function onProgress(time) {
  let progressBar = document.querySelector(".loader-progress");
  let progress = 0;
  let targetProgress = 95;
  let duration = time * 1000;
  let interval = setInterval(function () {
    progress++;
    progressBar.style.width = progress + "%";
    if (progress >= targetProgress) {
      clearInterval(interval);
    }
  }, duration / targetProgress);
}

function endProgress() {
  let progressBar = document.getElementById("customProgressBar");
  let progress = document.querySelector(".loader-progress");
  progress.style.width = "100%";
  clearInterval();
  if (progressBar) {
    setTimeout(function () {
      progress.style.width = "0%";
      if (progressBar.parentNode) {
        progressBar.parentNode.removeChild(progressBar);
      }
    }, 200);
  }
}

function getDistinctProducts(variants) {
  const uniqueProductsIds = new Set();
  return variants.filter(variant => {
    if (!uniqueProductsIds.has(variant.product_id)) {
      uniqueProductsIds.add(variant.product_id);
      return true;
    }
    return false;
  });
}

const MAIN_SERVER_URL = "https://remix-server-1053059746212.us-east1.run.app";

// const errorHandleNotifications = {
//   "billing failed": "This feature is disabled now. Please contact store owner to use this feature.",
//   "image error": "There are more than one face in the photo.",
//   "timeout error": "The AI server is currently experiencing technical difficulties. Please retry later.",
//   "unknown error": "Please be advised that there is an issue with the AI server.",
//   "match error": "The match result is not available. Please get in touch with the store administrator for further assistance.",
//   "no registered": "The registration process for products has not yet commenced on the AI server. Please get in touch with the store administrator for further assistance.",
//   "ai response failed": "Unexpected response from ai server. Please get in touch with the store administrator for further assistance.",
//   "request failed": "It seems that the request is incorrect. Please contact the store administrator for further assistance.",
//   "no sort products": "No recommended products by GYU are available at the moment.",
// };

const errorHandleNotifications = {
  "billing failed": "Please get in touch with the store administrator to use this feature",
  "image error": "There are more than one face in the photo.",
  "timeout error": "Please get in touch with the store administrator to use this feature.",
  "unknown error": "Please get in touch with the store administrator to use this feature.",
  "match error": "Please get in touch with the store administrator to use this feature.",
  "no registered": "Please get in touch with the store administrator to use this feature.",
  "ai response failed": "Please get in touch with the store administrator to use this feature.",
  "request failed": "Please get in touch with the store administrator to use this feature.",
  "no sort products": "Please get in touch with the store administrator to use this feature.",
};

const warningNotifications = {
  "missing selfie": "Please upload your selfie to use this feature."
};

function hexToRgb(hex) {
  const bigint = parseInt(hex.slice(1), 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return [r, g, b];
}

function rgbToHex(r, g, b) {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

function interpolateColor(color1, color2, factor) {
  const result = color1.slice();
  for (let i = 0; i < 3; i++) {
      result[i] = Math.round(result[i] + factor * (color2[i] - color1[i]));
  }
  return result;
}

function generateGradientColors(startColor, endColor, numColors) {
  const startRgb = hexToRgb(startColor);
  const endRgb = hexToRgb(endColor);
  const colors = [];

  for (let i = 0; i < numColors; i++) {
      const factor = i / (numColors - 1);
      const rgb = interpolateColor(startRgb, endRgb, factor);
      colors.push(rgbToHex(...rgb));
  }

  return colors;
}
