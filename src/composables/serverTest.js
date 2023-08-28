import axios from "axios"

const serverTest = async () => {

    return axios.get("http://localhost:5000/servertest").then((d)=>{
        console.log(d.data.message)
        if (d.status == 200){
            return true;
        }
    }).catch((e)=>{
        if (e.response && e.response.data.message) console.error(e.response.data.message);
        else console.error(e);
        return false;
    })
    
}

export default serverTest