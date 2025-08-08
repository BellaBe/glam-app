// import { json, unstable_createMemoryUploadHandler, unstable_parseMultipartFormData } from "@remix-run/node";
// import { getDownloadURL, getStorage, ref, uploadBytes, uploadString } from "firebase/storage";
// import { ai_server_selfie_register } from "../constant";
// import { isValidBilling } from "../utils/billingConfig";
// import firebase from "../utils/firebase";
// import { fetchWithTimeout } from "../utils/functions";

// /**
//  * Uploads a file or a captured image URL to Firebase Storage and returns the download URL.
//  * 
//  * @param {File | null} file - The file to be uploaded (if available).
//  * @param {string} selfie_id - A unique identifier for the storage reference (e.g., user ID or selfie ID).
//  * @param {string} capturedURL - A data URL string representing the captured image, used if file is not provided.
//  * @returns {Promise<string>} - A promise that resolves to the download URL of the uploaded file.
//  * 
//  */
// async function uploadFile(file, selfie_id, capturedURL) {
//   const storage = getStorage(firebase);
//   const storageRef = ref(storage, selfie_id);
//   let fileRef = null;
//   if (file)
//     fileRef = await uploadBytes(storageRef, file);
//   else
//     fileRef = await uploadString(storageRef, capturedURL, 'data_url');
//   const downloadURL = await getDownloadURL(fileRef.ref);
//   return downloadURL;
// }

// /**
//  * Processes a request from the storefront to the Remix server to upload a selfie, validate billing, and register the selfie via an AI server.
//  * 
//  * @param {Object} request - Incoming request containing multipart form data (selfie_id, shop_id, jpegFile, capturedURL).
//  * @param {Object} params - Additional parameters from the route.
//  * 
//  * @returns {Response} - JSON response with either the registered selfie details or an error status.
//  */
// export const action = async ({ request, params }) => {
//   const uploadHandler = unstable_createMemoryUploadHandler({
//     maxPartSize: 10000000, // Maximum file size of 10 MB
//   });
//   try {
//     const formData = await unstable_parseMultipartFormData(
//       request,
//       uploadHandler // <-- we'll look at this deeper next
//     );
//     let selfie_url = '';
//     let selfie;
//     const selfie_id = formData.get("selfie_id");
//     const shop_id = formData.get("shop_id");
//     const avatar = formData.get("jpegFile");
//     const isValid = await isValidBilling(shop_id);

//     // Validate billing for the shop
//     if (!isValid) {
//       return json({ error: "billing failed" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }

//     // Upload selfie image (either jpegFile or capturedURL)
//     if (avatar)
//       selfie_url = await uploadFile(avatar, selfie_id, '');
//     else {
//       const capturedURL = formData.get("capturedURL");
//       selfie_url = await uploadFile(null, selfie_id, capturedURL);
//     }

//     const options = {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//         "apikey": process.env.API_KEY
//       },
//       body: JSON.stringify({
//         selfie_id,
//         selfie_url,
//         shop_id
//       }),
//     };

//     console.log({selfie: options});

//     let responseData, response;  
//     try {
//       response = await fetchWithTimeout(ai_server_selfie_register, options, 20000); // 5000 ms timeout
//       if (!response.ok) {
//         throw new Error(`Server responded with status ${response.status}`);
//       }
//       responseData = await response.json();
//     } catch (error) {
//       if (error.message === 'Fetch request timed out') {
//         return json({ error: "timeout error" }, {
//           headers: {
//             "Access-Control-Allow-Origin": "*",
//           },
//         });
//       } else {
//         return json({ error: "ai response failed" }, {
//           headers: {
//             "Access-Control-Allow-Origin": "*",
//           },
//         });
//       }      
//     }
//     console.log("responseData error: ", {responseData});
//     if (responseData) {
//       if (responseData.status == "fail") {
//         return json({ error: responseData.error, fail: "fail" }, {
//           headers: {
//             "Access-Control-Allow-Origin": "*",
//           },
//         });
//       } else {
//         selfie = {
//           url: selfie_url,
//           url_image_mesh: responseData.url_image_mesh,
//           url_image_colorbars: responseData.url_image_colorbars,
//           description: responseData.description,
//           recommendation: responseData.recommendation
//         };
//       }      
//     } else {
//       return json({ error: "ai response failed" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }

//     return json({ selfie }, {
//       headers: {
//         "Access-Control-Allow-Origin": "*",
//       },
//     });
//   } catch (error) {
//     console.error("Error parsing multipart form data:", error);
//     return json({ error: "request failed" }, {
//       headers: {
//         "Access-Control-Allow-Origin": "*",
//       },
//     });
//   }
// }
