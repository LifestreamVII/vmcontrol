import axios from "axios"
import localforage from "localforage"


const killQemu = async () => {
    
    const getToken = async () => {
      try{
        const res = localforage.getItem('access_token')
          .then((token) => {
              if (!token){
                return null;
              }
              else 
              {
                return token;
              }
            })
            .catch((error) => {
              console.error(`Error while getting token : ${error}`);
            });
          return res;
        }
        catch (e){
          console.error(e);
        }
    }
  
    const token = await getToken();
    
    return axios.post("http://vmcontrol:5000/powerqemu", {
        data: { vmid: "100", action: "stop" },
        headers: { 'Authorization': `Bearer ${token}` }
    }).then((d)=>{
        console.log(d.data.message)
        if (d.data.statusUrl){
                    return d.data.statusUrl;
        } else if (d.data.statusUrlWOL && d.data.statusUrlPing){
            return [d.data.statusUrlWOL, d.data.statusUrlPing]
        }
    }).catch((e)=>{
        if (e.response && e.response.data.message) console.error(e.response.data.message);
        else console.error(e);
        return false;
    })
    
}

export default killQemu