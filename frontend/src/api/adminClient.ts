import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api/admin`;

export const adminClient = (adminEmail: string) => {
  return axios.create({
    baseURL: API_BASE,
    headers: { "X-Admin-Email": adminEmail || "" }
  });
};