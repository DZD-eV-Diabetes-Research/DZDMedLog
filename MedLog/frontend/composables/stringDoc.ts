export const useStringDoc = (ugly_name: string): string => {
    let beautiful_name = ugly_name.replaceAll("-"," ")
    const words = beautiful_name.split(" ");
        const capitalizedWords = words.map(word => {
        return word.charAt(0).toUpperCase() + word.slice(1);
    });
        return capitalizedWords.join(" ");
};