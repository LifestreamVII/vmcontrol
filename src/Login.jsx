import React from 'react'
import { useState } from 'react';
import axios from 'axios'; // You'll need axios or another HTTP library for API requests
import localforage from 'localforage';
import PulseLoader from "react-spinners/PulseLoader";

function Login() {
    
    const [loading, setLoading] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [token, setToken] = useState('');

    const handleSubmit = async (e) => {
        setLoading(true);
        e.preventDefault();

        try {
            setError('');
            const response = await axios.post('http://localhost:5000/login', { username, password });
            const { access_token } = response.data;
            setToken(access_token);
            saveToken(access_token);
            window.location.href = "";
        } catch (error) {
            setError('Invalid credentials');
        }
        setLoading(false);
    };

    const saveToken = async (token) => {
        return localforage.setItem('access_token', token)
            .then(() => true)
            .catch((error) => {
                console.error(`Error while saving token : ${error}`);
            });
    }

  return (
    <div className='Login'>
        <div className='row mb-m'>
            <div className='col-10'>
                <a href="https://www.youtube.com/watch?v=WI1akmLeYYY">
                    <img className='homeImg' src="miku.jpg" alt="" />
                </a>
            </div>
        </div>
        <div className='row'>
            <div className='col-12'>
                <input type="text" required name="username" id="" value={username} onChange={(e) => setUsername(e.target.value)} placeholder='login' />
            </div>
        </div>
        <div className='row'>
            <div className='col-12'>
                <input type="password" required name="password" value={password} onChange={(e) => setPassword(e.target.value)} name="" id="" placeholder='pass' />
            </div>
        </div>
        <div className='row'>
            <div className='col-12'>
                <button type="submit" className="contrast" onClick={handleSubmit}>Login</button>
            </div>
        </div>
        {
            error && !loading ? (
                <div className='row'>
                    <div className='col-12'>
                        <p>{error}</p>
                    </div>
                </div>
            ) : ""
        }
        {
            loading ? (
                <div className='row'>
                    <div className='col-12 col-md-4'>
                        <PulseLoader
                            color="#fff"
                            size={10}
                            loading={loading}
                        />
                    </div>
                </div>
            ) : ""
        }
    </div>
  )
}

export default Login