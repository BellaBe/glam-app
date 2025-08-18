// import { json } from "@remix-run/node";
// import { getProductFromImageId } from "../models/gyuProducts.store";
// import { ai_server_match_analysis } from "../constant";
// import { isValidBilling } from "../utils/billingConfig";
// import { fetchWithTimeout } from "../utils/functions";
// /**
//  * This route handles requests from the storefront to the Remix server,
//  * performing an AI-based product matching and analysis based on provided data.
//  *
//  * Expected Request Payload:
//  * @request matchData - An object containing:
//  *   - shop_id (string): ID of the Shopify store
//  *   - image_id (string): ID of the product image
//  *   - product_id (string): ID of the product
//  */
// export const action = async ({ request, params }) => {
//   try {
//     const form = await request.formData();
//     const matchData = JSON.parse(form.get("matchData"));
//     // Check billing status for the shop to ensure they have an active subscription
//     const isValid = await isValidBilling(String(matchData.shop_id));
//     if (!isValid) {
//       return json({ error: "billing failed" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }
//     for (let key in matchData) {
//       if (typeof matchData[key] === 'number') {
//         matchData[key] = matchData[key].toString();
//       }
//     }

//     // Retrieve the product associated with the given image ID and shop
//     const matchedProduct = await getProductFromImageId(matchData);
//     if (matchedProduct == null) {
//       return json({ error: "no registered" }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }

//     const options = {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//         "apikey": process.env.API_KEY
//       },
//       body: JSON.stringify({
//         ...matchData,
//         variant_id: matchedProduct.variant_id
//       }),
//     };

//     let responseData, response;

//     try {
//       response = await fetchWithTimeout(ai_server_match_analysis, options, 15000); // 5000 ms timeout
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

//     // If AI response is received, format and return the data to the storefront
//     if (responseData) {
//       return json({
//         score_color: (responseData.score_color) / 20,
//         score_morph: (responseData.score_morph) / 20,
//         score_overall: (responseData.score_overall) / 20,
//         recommendation: responseData.recommendation,
//         description: responseData.description,
//       }, {
//         headers: {
//           "Access-Control-Allow-Origin": "*",
//         },
//       });
//     }
//   } catch (error) {
//     console.error("Error parsing multipart form data:", error);
//     return json({ error: "request failed" }, {
//       headers: {
//         "Access-Control-Allow-Origin": "*",
//       },
//     });
//   }
// }
