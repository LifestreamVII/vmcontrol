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
    
    return axios.get("http://localhost:5000/killqemu", {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then((d)=>{
        console.log(d.data.message)
        if (d.status == 200 && d.data.message){
            switch (d.data.message) {
                case "OK" :
                    return d.data.status_url;
                    break;
                default :
                    return false;
                    break;
            }
        } else return false;
    }).catch((e)=>{
        if (e.response && e.response.data.message) console.error(e.response.data.message);
        else console.error(e);
        return false;
    })
    
}

export default killQemu