package de.dzd.medlog.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@Slf4j
public class CorsConfig implements WebMvcConfigurer {

    @Value("${frontend.url.prod}")
    String origin;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        log.info("Adding the following origin to CorsRegistry: " + origin);
        registry.addMapping("/**")
                .allowedOrigins(origin)
                .allowedMethods("*");
    }

}
