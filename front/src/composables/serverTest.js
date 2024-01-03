import axios from "axios"

const serverTest = async () => {

    return axios.get("/api/servertest").then((d)=>{
        console.log(d.data.message)
        if (d.status == 200){
            return 200;
        } else return 1;
    }).catch((e)=>{
        if (e.response && e.response.data.message) console.error(e.response.data.message);
        else console.error(e);
        return 1;
    })
    
}

export default serverTest
