export const useGetCurrentDate = () => {

    let today = new Date();
    let year = today.getFullYear();
    let month = String(today.getMonth() + 1).padStart(2, '0'); 
    let day = String(today.getDate()).padStart(2, '0');
    let hour = today.getHours();
    let minutes = String(today.getMinutes()).padStart(2, '0');
    let seconds = String(today.getSeconds()).padStart(2, '0');
    let milliSeconds = String(today.getMilliseconds()).padStart(3, '0');

    today = year+"-"+month+"-"+day+"T"+hour+":"+minutes+":"+seconds+"."+milliSeconds+"Z"
    return today
}