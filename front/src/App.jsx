import './App.css';
import { useState } from 'react';
import axios from 'axios'; // You'll need axios or another HTTP library for API requests
import localforage from 'localforage';
import Login from './Login';
import Home from './Home';
import PulseLoader from "react-spinners/PulseLoader";


function App() {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(true);

  const getToken = async () => {
    try{
      const res = localforage.getItem('access_token')
        .then((token) => {
            if (!token){
              setToken(null);
            }
            else 
            {
              setToken(token);
            }
            setLoading(false);
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

  getToken();

  return (
    <div className="App container">
      

      <PulseLoader
        color="#fff"
        size={10}
        loading={loading}
      />

      {
        !loading ? (token ? (<Home></Home>)
        : (<Login></Login>)) : ""
      }
    </div>
  );
}

export default App;
