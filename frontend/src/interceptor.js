import axios from "axios";
import store from "./store";

let refresh = false;

axios.interceptors.response.use(resp => resp, async error => {
    if (error.response.status === 401 && !refresh) {
        refresh = true;

        const refresh_token = store.getters.refresh_token
        console.log("Old Token "+store.getters.access_token)


        axios.defaults.headers.common = { 'refresh-token': "Bearer " + refresh_token }

        const { status, data } = await axios.post('/auth/refresh', {
            headers: {
                'Content-Type': 'json',
            }
        }, {
            withCredentials: true
        });

        if (status === 200) {
            //Token
            store.dispatch('updateAccessToken', data.access_token )
            // axios.defaults.headers.common = {'Authorization' : "Bearer " + data.access_token}

            error.config.headers = {'Authorization' : "Bearer " + data.access_token}
            return axios(error.config);
        }
    }
    refresh = false;
    return error;
});