import axios from "axios";

const API_BASE_URL = "http://localhost:8080/api/tests";

// GET all tests
export const getAllTests = async () => {
  return await axios.get(API_BASE_URL);
};

// GET single test
export const getTestById = async (id) => {
  return await axios.get(`${API_BASE_URL}/${id}`);
};

// ADD new test
export const addTest = async (testData) => {
  return await axios.post(API_BASE_URL, testData);
};

// UPDATE existing test
export const updateTest = async (id, testData) => {
  return await axios.put(`${API_BASE_URL}/${id}`, testData);
};