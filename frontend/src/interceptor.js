import axios from "axios";
import router from "./router";
import { useTokenStore } from '@/stores/TokenStore'
import { useUserStore } from '@/stores/UserStore'


let refresh = false;

function setupInterceptor() {
    axios.interceptors.response.use(
        (response) => response,
        async (error) => {
            if (error.response && error.response.status === 401 && !refresh) {
                refresh = true;

                const tokenStore = useTokenStore()
                const refresh_token = tokenStore.get_refresh_token

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

                        tokenStore.access_token = data.access_token
                        error.config.headers = {
                            Authorization: "Bearer " + tokenStore.get_access_token,
                        };
                        refresh = false;
                        return axios(error.config);
                    }
                } catch (refreshError) {
                    const userStore = useUserStore()
                    refresh = false;
                    tokenStore.$reset()
                    userStore.$reset()
                    router.push("/");
                    return Promise.reject(refreshError);
                }
            }
            refresh = false;
            return Promise.reject(error);
        }
    );
}

setupInterceptor(); 

export default setupInterceptor; 