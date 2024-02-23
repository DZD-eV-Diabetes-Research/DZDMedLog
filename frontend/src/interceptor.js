// import axios from "axios";
// import store from "./store";
// import router from "./router"; // Import Vue Router instance

// let refresh = false;

// axios.interceptors.response.use(resp => resp, async error => {
//     if (error.response.status === 401 && !refresh) {
//         refresh = true;

//         const refresh_token = store.getters.refresh_token

//         axios.defaults.headers.common = { 'refresh-token': "Bearer " + refresh_token }

//         const { status, data } = await axios.post('/auth/refresh', {
//             headers: {
//                 'Content-Type': 'json',
//             }
//         }, {
//             withCredentials: true
//         });

//         if (status === 200) {
//             //Token
//             store.dispatch('updateAccessToken', data.access_token )
//             // axios.defaults.headers.common = {'Authorization' : "Bearer " + data.access_token}

//             error.config.headers = {'Authorization' : "Bearer " + data.access_token}
//             return axios(error.config);
//         }
//     }
//     refresh = false;
//     return error;



// });

import axios from "axios";
import store from "./store";
import router from "./router"; // Import Vue Router instance

let refresh = false;

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401 && !refresh) {
      refresh = true;

      const refresh_token = store.getters.refresh_token;

      axios.defaults.headers.common = {
        "refresh-token": "Bearer " + refresh_token,
      };

      try {
        const { status, data } = await axios.post(
          "/auth/refresh",
          {},
          {
            headers: {
              "Content-Type": "json",
            },
            withCredentials: true,
          }
        );

        if (status === 200) {
          store.dispatch("updateAccessToken", data.access_token);
          error.config.headers = {
            Authorization: "Bearer " + data.access_token,
          };
          refresh = false;
          return axios(error.config);
        }
      } catch (refreshError) {
        refresh = false;
        router.push("/auth");
        return Promise.reject(refreshError);
      }
    }
    refresh = false;
    return Promise.reject(error);
  }
);

