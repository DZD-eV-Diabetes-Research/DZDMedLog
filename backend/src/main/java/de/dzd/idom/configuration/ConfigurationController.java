package de.dzd.idom.configuration;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/configuration")
@RequiredArgsConstructor
@Slf4j
public class ConfigurationController {

    private final ConfigurationService configurationService;
    private final ImportParser importParser;


    @PostMapping
    public ResponseEntity<Configuration> uploadFile(@RequestParam("file") MultipartFile file) throws IOException {
        Configuration uploadFile = configurationService.uploadFile(file);
        importParser.createAndSaveNewDrugs(uploadFile);
        return new ResponseEntity<>(uploadFile, HttpStatus.OK);
    }

    @GetMapping("/{fileName}")
    public ResponseEntity<?> dowloadFile(@PathVariable String fileName) {
        byte[] fileData = configurationService.downloadFile(fileName);

        if (fileData.length == 0) {
            return ResponseEntity.notFound().build();
        } else {
            return ResponseEntity.status(HttpStatus.OK)
                    .contentType(MediaType.valueOf("zip"))
                    .body(fileData);
        }
    }
}
