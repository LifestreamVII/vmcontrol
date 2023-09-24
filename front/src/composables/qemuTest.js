import axios from "axios";
import localforage from "localforage";

const qemuTest = async () => {
  try {
    const token = await getToken();

    const { data } = await apiToSpawnTask(token);
    const taskId = data.statusUrl;
    const status = await checkTaskStatus(taskId);

    return status;
  } catch (error) {
    console.error("Error in qemuTest:", error);
    throw error;
  }
}

async function getToken() {
  try {
    const token = await localforage.getItem("access_token");
    return token || null;
  } catch (error) {
    console.error("Error while getting token:", error);
    throw error;
  }
}

async function apiToSpawnTask(token) {
  try {
    const response = await axios.get("/api/checkqemu", {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log(response.data);

    return response;
  } catch (error) {
    console.error("Error in apiToSpawnTask:", error);
    throw error;
  }
}

async function checkTaskStatus(url) {
  try {
    let status;

    while (true) {
      const { data } = await axios.get(url);
	  console.log(data);
      if (data.state === "SUCCESS") {
        status = await getCompletedTaskResult(url);
        break;
      }

      // Sleep for 5 seconds before checking again
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }

    return status;
  } catch (error) {
    console.error("Error in checkTaskStatus:", error);
    throw error;
  }
}

async function getCompletedTaskResult(url) {
  try {
    const { data } = await axios.get(url);
	console.log(data);
    return data.status;
  } catch (error) {
    console.error("Error in getCompletedTaskResult:", error);
    throw error;
  }
}

export default qemuTest;