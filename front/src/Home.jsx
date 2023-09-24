import { useState, useEffect } from 'react';


import localforage from 'localforage';


import { Windmill, Squares } from "react-activity";


import "react-activity/dist/library.css";


import serverTest from './composables/serverTest';


import qemuTest from './composables/qemuTest';


import qemuOn from './composables/qemuOn';



const Home = () => {


    const logout = async () => {


        try {


            await localforage.removeItem("access_token");


            window.location.href = "";


        } catch (error) {


        }


    };



    const [loading, setLoading] = useState(false);


    const [VM, setVM] = useState({});


    const [progress, setProgress] = useState([]);


    const [QEMU, setQEMU] = useState(false);


    const RadioInput = ({ label, value, checked, setter }) => {


        return (


            <label>


                <input type="radio" checked={checked === value}


                    onChange={() => setter(value)} />


                <span>{label}</span>


            </label>


        );


    };



    const VMs = {


        100:


        {


            name: "Win10 Gaming",


            specs: "i5 12400F - GTX 1660 - 8 GB RAM - 256 GB",


            vmid: 100


        },


        101:


        {


            name: "Win10 Desktop Lt.",


            specs: "i5 12400F - GTX 1660 - 4 GB RAM - 120 GB",


            vmid: 101


        },


        102:


        {


            name: "Win10 Minimum",


            specs: "i5 12400F - No GPU - 4 GB RAM - 120 GB",


            vmid: 102


        },


        103:


        {


            name: "Kali Linux",


            specs: "i5 12400F - No GPU - 6 GB RAM - 120 GB",


            vmid: 103


        },


        200:


        {


            name: "Win11 Basic",


            specs: "Ryzen 5700G - iGPU - 12 GB RAM - 120 GB",


            vmid: 200


        }


    }



    const turnOnVM = async (info) => {


        if (window.confirm(`


        Requested ${VMs[VM].name} to be turned on.\n


        This may take a few minutes.\n


        Specs : ${VMs[VM].specs}\n


        Confirm ? 


        `)) {


            try {


                // Turn on VM


                console.log('Turn ON VM Request.');


                setLoading(true);



                progress.push("Contacting server...");


                const isReachable = await serverTest();


                if (isReachable == 200) {


                    console.log(true);



                    progress.push("Server reached successfully.");



                    if (QEMU !== "isON" || QEMU !== "isONROO") {

                        let p = [];



                        progress.push("Turning ON virtual env...");


                        const updateStatus = (newStatus) => {

                            p.push(newStatus);

                            setProgress([...progress, newStatus]);

                        };



                        qemuOn(updateStatus, VMs[VM].vmid, "start").catch((error) => {

                            console.error("Error in qemuOn:", error);

                        });



                    } else throw Error("QEMU is already running.");




                } else {
                    
                    let p = [];
                    p.push("Server is unreachable, trying WoL...");
                    setProgress([...progress, "Server is unreachable, trying WoL..."]);

                    const updateStatus = (newStatus) => {
                        p.push(newStatus);
                        setProgress([...progress, newStatus]);
                    };

                    qemuOn(updateStatus, VMs[VM].vmid, "start").then((d)=>{
                        console.log("finished");
                        console.log(d);
                    }).catch((error) => {

                        console.error("Error in qemuOn:", error);

                    });

                }


            } catch (e) {

                setLoading(false);
                setProgress([...progress, e]);

             }
    }
}

const killQEMU = async () => {


    if (window.confirm(`


        Requested QEMU forced shutdown.\n


        This may lead to file corruption.\n


        Confirm ?


        `)) {

            try{

                setLoading(true);

                let p = [];

                progress.push("Killing virtual env...");
                const updateStatus = (newStatus) => {

                    p.push(newStatus);

                    setProgress([...progress, newStatus]);

                };

                qemuOn(updateStatus, 100, "stop").catch((error) => {

                    console.error("Error in qemuOn:", error);

                });

            } catch(e){
                setLoading(false);
                setProgress([...progress, e]);
            }



    } else {


        // Do nothing


        console.log('Action aborted by user');


    }


}



useEffect(() => {

    let ignore = false;



    if (!ignore) {

        qemuTest().then((s) => {

            console.log(s);

            setQEMU(s);

        });

    }



    return () => {

        ignore = true;

    }

}, [])




return (


    <div className='Home'>


        <header>


            <div class="navbar">


                <div class="navbar__middle">


                    <a href="" class="navbar__link">


                        Home


                    </a>


                </div>


                <div class="navbar__right">


                    <button type="button" onClick={logout}>Logout</button>


                </div>


            </div>


        </header>


        <div className='main mt-xl'>


            <h2>VM Control Panel</h2>


            {


                !loading ? (


                    <section id="buttons">


                        <div className='row'>


                            {

                                QEMU === "isON" ? (

                                    <div className='col-12 mb-s'>

                                        <Windmill className='mr-es' color="white" style={{ "display": "inline-block", "verticalAlign": "middle" }} />

                                        <span>QEMU Host Service is running</span>

                                    </div>

                                ) : (

                                    QEMU === "isOFF" ? (

                                        <div className='col-12 mb-s'>

                                            <span>✓ QEMU Host Service is not running</span>

                                        </div>

                                    ) : (

                                        QEMU === "isONROOT" ? (

                                            <div className='col-12 mb-s'>

                                                <span>✖ QEMU Host Service is running with root privileges</span>

                                            </div>

                                        ) : (

                                            <div className='col-12 mb-s'>

                                                <span>QEMU status cannot be retrieved at the moment</span>

                                            </div>

                                        )

                                    )

                                )

                            }


                        </div>


                        <div class="grid">


                            {Object.entries(VMs).map(([key, value]) => {


                                return (


                                    <div>


                                        <RadioInput label={value.name} value={key} checked={VM} setter={setVM} />


                                    </div>


                                )


                            })}


                        </div>


                        <button disabled={QEMU == "isONROOT" || QEMU == "isON"} onClick={() => turnOnVM(VM)}>OK</button>


                        {


                            QEMU === "isON" ? (


                                <div className='grid'>


                                    <button onClick={killQEMU} style={{ backgroundColor: "crimson", border: "none" }}>Kill QEMU</button>


                                </div>


                            ) : ("")


                        }


                    </section>





                ) : (


                    <div>


                        <div>


                            <Squares className='mr-es' color="white" /><span>Loading</span>


                        </div>


                        <div>


                            {progress.map((value, index) => {


                                return (


                                    <p>{value}</p>


                                )


                            })}


                        </div>


                    </div>


                )


            }


        </div>


    </div>


)


}



export default Home

