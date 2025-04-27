import axiosClient from "../axios/client";

export const AuthApi = {
    async ping() : Promise<string> {
        const res = await axiosClient.post<string>("/api/v1/users/ping");
        return res.data;
    }
}