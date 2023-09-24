import axios from "axios";
import localforage from "localforage";

const qemuOn = async (progress, vmid='100', action="start") => {
  try {
    const token = await getToken();

    const { data } = await apiToSpawnTask(token, vmid.toString(), action);
	if (data.statusUrl) {
		const taskId = data.statusUrl;
		await checkTaskStatus(taskId, false, progress);
	} else if (data.statusUrlWOL || data.statusUrlPing || data.status == "PINGFAIL"){
		const taskIdW = data.statusUrlWOL;
		const taskIdP = data.statusUrlPing;
		await checkTaskStatus(taskIdW, taskIdP, progress);
	} else {
		throw Error("Couldn't determine the server's state");
	}
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

async function apiToSpawnTask(token, vmid, action) {
  try {
    const response = await axios.post("/api/powerqemu", {vmid: vmid, action: action},
      {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log(response.data);

    return response;
  } catch (error) {
    console.error("Error in apiToSpawnTask:", error);
    throw error;
  }
}

async function checkTaskStatus(url, url2=false, progress) {
  try {
    let status = "";
    let step = 0;
    while (true) {
	  if (!url2){
		  const { data } = await axios.get(url);
		  console.log(data);
		  status = data.status ?? "Please wait...";
		  if (data.state === "SUCCESS") {
			status = await getCompletedTaskResult(url);
			break;
		  }
		  
		  progress(status);

		  // Sleep for 5 seconds before checking again
		  await new Promise((resolve) => setTimeout(resolve, 700));
	  }
	  
	  else {
		  if (step < 1) { 
        const { data: wol } = await axios.get(url); 
		    status = wol.status ?? "Please wait...";
        if (wol.state === "SUCCESS") {
          status = "WoL command sent";
          step = 1;
        }
      }
		  const { data: ping } = await axios.get(url2);
      status = ping.status ?? "Please wait...";
      if (ping.state === "SUCCESS") {
        status = "Ping reached server";
        step = 2;
        status = await getCompletedTaskResult(url2);
        break;
      }
		  
		  progress(status);

		  // Sleep for 5 seconds before checking again
		  await new Promise((resolve) => setTimeout(resolve, 700));
	  }
    }

    progress(status);
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

export default qemuOn;
