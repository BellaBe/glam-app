// import { json } from "@remix-run/node";
// import { deleteObject, getStorage, ref } from "firebase/storage";
// import firebase from "../utils/firebase";

// /**
//  * Deletes a file from Firebase Storage given its URL.
//  *
//  * @param {string} fileUrl - The URL of the file to be deleted.
//  * @returns {void}
//  */
// async function deleteFileByUrl(fileUrl) {
//   const storage = getStorage(firebase);
//   const fileRef = ref(storage, fileUrl);

//   try {
//     await deleteObject(fileRef);
//   } catch (error) {
//   }
// }

// /**
//  * Handles the request from the storefront to the Remix server for deleting a selfie file.
//  * @request Multipart form data containing:
//  * - `selfieUrl` (string): Firestore URL of the selfie image to delete.
//  *
//  * @returns JSON response:
//  * - `{ ok: "ok" }` with status 200 and CORS headers on success.
//  * - `{ status: 411 }` on failure, with CORS headers.
//  */
// export const action = async ({ request, params }) => {
//   try {
//     const form = await request.formData();
//     const selfieUrl = form.get("selfieUrl");
//     await deleteFileByUrl(selfieUrl);
//     return json({ ok: "ok" }, {
//       headers: {
//         "Access-Control-Allow-Origin": "*",
//       },
//     });
//   } catch (error) {
//     return json({ error: "request failed" }, {
//       headers: {
//         "Access-Control-Allow-Origin": "*",
//       },
//     });
//   }
// }
