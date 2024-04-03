import axios, { AxiosError, AxiosRequestHeaders } from "axios";
import router from "@/router";
import { useTokenStore } from '@/stores/TokenStore'
import { useUserStore } from '@/stores/UserStore'

let refresh = false;

function setupInterceptor(): void {
    axios.interceptors.response.use(
        (response) => response,
        async (error: AxiosError) => {
            if (error.response && error.response.status === 401 && !refresh) {
                refresh = true;

                const tokenStore = useTokenStore();
                const refresh_token = tokenStore.refreshToken;

                axios.defaults.headers.common = {
                    "refresh-token": "Bearer " + refresh_token,
                };

                try {
                    const { status, data } = await axios.post(
                        "/auth/refresh",
                        {},
                        {
                            headers: {
                                "Content-Type": "application/x-www-form-urlencoded",
                            },
                            withCredentials: true,
                        }
                    );

                    if (status === 200) {
                        tokenStore.accessToken = data.access_token;
                        if (error.config) {
                            error.config.headers = {
                                Authorization: "Bearer " + tokenStore.accessToken,
                            } as AxiosRequestHeaders;
                            refresh = false;
                            return axios(error.config);
                        }
                    }
                } catch (refreshError) {
                    const userStore = useUserStore();
                    refresh = false;
                    tokenStore.$reset();
                    userStore.$reset();
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
