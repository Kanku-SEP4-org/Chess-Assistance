import axios from "axios";

const API_URL = "http://localhost:3001/tests";

export const addTest = async (testData) => {
  return await axios.post(API_URL, testData);
};