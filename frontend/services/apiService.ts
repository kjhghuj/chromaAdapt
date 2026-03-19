import { StyleConfig, TargetFont } from '../types';
import { resizeImage } from '../utils/imageHelpers';

const BACKEND_URL = 'http://localhost:8000';

const cleanBase64 = (base64: string) => base64.replace(/^data:image\/[a-z]+;base64,/, '');

export const analyzeImageColors = async (imageData: string, language: string, model: string) => {
  // Resize for faster analysis
  const resizedImage = await resizeImage(imageData, 800, 800);
  
  const response = await fetch(`${BACKEND_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      image: cleanBase64(resizedImage),
      prompt: `分析这张图片的色彩、构图和主要内容。请以JSON格式返回色盘，包含一个名为 "palette" 的数组，数组中包含5个十六进制颜色代码。`
    }),
  });
  const data = await response.json();
  // Expecting { palette: ["#...", "#...", ...] }
  const content = data.choices[0].message.content;
  
  // Clean potential markdown blocks
  let cleanJson = content.trim();
  if (cleanJson.includes('```json')) cleanJson = cleanJson.split('```json')[1].split('```')[0].strip();
  else if (cleanJson.includes('```')) cleanJson = cleanJson.split('```')[1].split('```')[0].strip();
  
  try {
    const result = JSON.parse(cleanJson);
    return result.palette || ["#000000", "#333333", "#666666", "#999999", "#CCCCCC"];
  } catch (e) {
    console.error("Failed to parse color palette", e);
    return ["#000000", "#333333", "#666666", "#999999", "#CCCCCC"];
  }
};

export const generatePosterAdaptation = async (posterData: string, palette: string[], styleConfig: StyleConfig, model: string) => {
  const prompt = `使用以下色盘对这张海报进行色彩适配: ${palette.join(', ')}。保持布局一致，替换主要色彩。`;
  const response = await fetch(`${BACKEND_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      prompt,
      image_urls: [`data:image/jpeg;base64,${cleanBase64(posterData)}`]
    }),
  });
  const data = await response.json();
  return data.data[0].url || posterData; // Return generated URL or fallback
};

export const generateImageTranslation = async (imageData: string, targetLang: string, targetFont: TargetFont, model: string): Promise<{ url: string; instructions?: any }> => {
  // Resize for faster OCR analysis
  const resizedImage = await resizeImage(imageData, 1024, 1024);

  const response = await fetch(`${BACKEND_URL}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image: cleanBase64(resizedImage),
      target_lang: targetLang,
      target_font: targetFont
    }),
  });
  const data = await response.json();

  // The backend returns { translation_instructions: {...}, result: {...} }
  // We extract the final image URL and pass the instructions for display
  const imageUrl = data.result?.data?.[0]?.url || imageData;
  return {
    url: imageUrl,
    instructions: data.translation_instructions
  };
};

export const generateProductReplacement = async (imageData: string, productPrompt: string, model: string) => {
  const prompt = `保持背景不变，将图中的产品替换为: ${productPrompt}。`;
  const response = await fetch(`${BACKEND_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      prompt,
      image_urls: [`data:image/jpeg;base64,${cleanBase64(imageData)}`]
    }),
  });
  const data = await response.json();
  return data.data[0].url || imageData;
};

export const generateImageEdit = async (imageData: string, editPrompt: string, model: string) => {
  const response = await fetch(`${BACKEND_URL}/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      image: cleanBase64(imageData),
      prompt: editPrompt
    }),
  });
  const data = await response.json();
  return data.data[0].url || imageData;
};

// Simplified placeholders for other functions used in hooks
export const generateSecondaryImage = async (imageData: string, plan: any, item: any, model: string) => imageData;
export const generateSecondaryImagePlan = async (imageData: string, palette: string[], model: string) => ({ items: [] });
export const analyzeAndCreateTranslationPrompt = async (imageData: string, targetLang: string, model: string) => "Translation prompt";
export const createColorMappingPlan = async (posterData: string, palette: string[], model: string) => "Color mapping plan";
export const generatePreciseAdaptation = async (posterData: string, plan: string, model: string) => posterData;
export const analyzeAndCreateEditPrompt = async (imageData: string, userInput: string, model: string) => userInput;
