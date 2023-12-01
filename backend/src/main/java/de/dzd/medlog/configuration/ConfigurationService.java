package de.dzd.medlog.configuration;

import de.dzd.medlog.util.FileCompressor;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Optional;

@Service
@AllArgsConstructor
public class ConfigurationService {

    private ConfigurationRepository repository;

    public Configuration uploadFile(MultipartFile file) throws IOException {
        return repository.save(Configuration.builder()
                .fileName(file.getOriginalFilename())
                .type(file.getContentType())
                .fileData(FileCompressor.compressFile(file.getBytes())).build());
    }

    public byte[] downloadFile(String fileName) {
        Optional<Configuration> dbfileData = repository.findByFileName(fileName);
        return dbfileData
                .map(configuration -> FileCompressor.decompressFile(configuration.getFileData()))
                .orElseGet(() -> new byte[0]);
    }
}