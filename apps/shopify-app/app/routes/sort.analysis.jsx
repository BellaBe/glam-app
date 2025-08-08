// import { json } from "@remix-run/node";
// import { ai_server_shop_sort } from "../constant";
// import { isValidBilling } from "../utils/billingConfig";
// import { getDistinctProducts } from "../utils/functions";
// import { getRegistered } from "../models/gyuProducts.store";

// /**
//  * Processes product sorting requests from the storefront to the Remix server.
//  * 
//  * @request Multipart form data with:
//  * - `selfie_id` (string): The ID for the selfie image.
//  * - `shop_id` (string): The shop's unique ID.
//  * - `gyu_products` (stringified JSON): Array of products to check against the database.
//  * 
//  * @returns JSON response:
//  * - `{ sorted_products }` with sorted products and CORS headers if sorting succeeds.
//  * - `{ success: "no update" }` if no update is needed.
//  * - `{ error: "billing failed" }` with CORS headers if billing is invalid.
//  * - `{ status: 413 }` if the AI server request fails.
//  * - `{ status: 411 }` if any other error occurs.
//  */
// export const action = async ({ request, params }) => {
//   try {
//     const form = await request.formData();
//     const isValid = await isValidBilling(String(form.get("shop_id")));
//     const selfie_id = form.get("selfie_id");
//     const shop_id = form.get("shop_id");   
//     if (!isValid) {
//       return json({ error: "billing failed" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }
//     // Compares the firebase products registered in the 'Analyzed' status with the cache products obtained from the ai server.
//     const gyuProducts = JSON.parse(form.get("gyu_products"));    
//     const variants = await getRegistered(shop_id);
//     let fDifferent = false;
//     const cntGyuProducts = getDistinctProducts(gyuProducts).length;
//     const cntFireProducts = getDistinctProducts(variants).length;
//     if (cntFireProducts == 0) {
//       return json({ success: "no registered" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }
//     // compare the amount of products
//     if (cntGyuProducts != cntFireProducts) fDifferent = true;
//     // compare the each product
//     else {
//       for (const gyuProduct of gyuProducts) {
//         const isRegistered = variants.find(variant => (variant.product_id == gyuProduct.product_id && variant.variant_id == gyuProduct.variant_id));
//         if (!isRegistered) {
//           fDifferent = true;
//           break;
//         }
//       }
//     }
//     if (!fDifferent) {
//       return json({ success: "no update" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }
//     let response = await fetch(
//       ai_server_shop_sort,
//       {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//           "apikey": process.env.API_KEY
//         },
//         body: JSON.stringify({
//           selfie_id,
//           shop_id
//         }),
//       },
//     );
//     let responseData = await response.json();
//     console.log({sort: responseData});
//     if (responseData) {
//       const sorted_products = responseData.sorted_products;
//       if (sorted_products.length == 0) {
//         return json({ success: "no registered" }, {
//           headers: {
//             "Access-Control-Allow-Origin": "*",
//           },
//         });
//       }
//       return json({ sorted_products }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     } else {
//       return json({ error: "ai response failed" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }
//   } catch (error) {
//     return json({ error: "request failed" }, {
//       headers: {
//         "Access-Control-Allow-Origin": "*",
//       },
//     });
//   }
// }
