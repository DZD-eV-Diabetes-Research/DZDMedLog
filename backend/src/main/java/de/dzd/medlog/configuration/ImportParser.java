package de.dzd.medlog.configuration;

import de.dzd.medlog.drug.Drug;
import de.dzd.medlog.drug.DrugService;
import de.dzd.medlog.drug.association.*;
import de.dzd.medlog.util.FileCompressor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.time.DurationFormatUtils;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.Files;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

@Service
@Slf4j
@RequiredArgsConstructor
public class ImportParser {

    private Map<String, String> csvStrings;
    private final String CSV_ROW_DELIMITER = "\n";
    private final String CSV_COLUMN_DELIMITER = ";";
    private final DrugService drugService;

    private final ATCRepository atcRepository;
    private Map<String, ATC> atcMap = new HashMap<>();

    private final DosageFormRepository dosageFormRepository;
    private Map<String, DosageForm> dosageFormMap = new HashMap<>();

    private final ApplicationFormRepository applicationFormRepository;
    private Map<String, ApplicationForm> applicationFormMap = new HashMap<>();

    private final NormPackageSizeRepository normPackageSizeRepository;
    private Map<String, NormPackageSize> normPackageSizeMap = new HashMap<>();

    private final ProducerRepository producerRepository;
    private Map<String, Producer> producerMap = new HashMap<>();

    public void createAndSaveNewDrugs(Configuration configuration) throws IOException {
        Instant start = Instant.now();
        log.info("Starting drug creation from import...");

        byte[] fileData = FileCompressor.decompressFile(configuration.getFileData());
        csvStrings = getCsvStrings(fileData);

        createAssociations();

        log.info("Creating drugs...");
        List<Drug> createdDrugs = Arrays.stream(csvStrings.get("stamm.txt").split(CSV_ROW_DELIMITER))
                .map(this::createDrug)
                .filter(Objects::nonNull).toList();
        drugService.saveAll(createdDrugs);

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        log.info("Created and saved {} new drugs [{}]", createdDrugs.size(), duration);
    }

    private Map<String, String> getCsvStrings(byte[] fileData) throws IOException {
        File file = File.createTempFile("stammdatei-plus", "zip");
        Files.write(file.toPath(), fileData);

        Map<String, String> csvStrings = new HashMap<>();
        ZipFile zipFile = new ZipFile(file);
        Enumeration<? extends ZipEntry> zipEntries = zipFile.entries();
        while (zipEntries.hasMoreElements()) {
            StringBuilder content = new StringBuilder();
            ZipEntry entry = zipEntries.nextElement();

            if (entry.getName().endsWith(".txt")) {
                InputStream inputStream = zipFile.getInputStream(entry);
                BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));

                String line;
                while ((line = reader.readLine()) != null) {
                    content.append(line).append("\n");
                }
                reader.close();

                int rootSlashIndex = !entry.getName().contains("/") ? 0 : entry.getName().indexOf("/");
                String fileName = entry.getName().substring(rootSlashIndex + 1);

                csvStrings.put(fileName, content.toString());
            }
        }
        return csvStrings;
    }

    private Drug createDrug(String csvRow) {
        String[] csvColumns = csvRow.split(CSV_COLUMN_DELIMITER);
        try {
            return Drug.builder()
                    .pharmaceuticalCentralNumber(Long.parseLong(csvColumns[7]))
                    .atc(atcMap.getOrDefault(csvColumns[5], null))
                    .name(csvColumns[8])
                    .dosageForm(dosageFormMap.getOrDefault(csvColumns[10], null))
                    .applicationForm(applicationFormMap.getOrDefault(csvColumns[24], null))
                    .packageSize(Integer.valueOf(csvColumns[12]))
                    .normPackageSize(normPackageSizeMap.getOrDefault(csvColumns[11], null))
                    .producer(producerMap.getOrDefault(csvColumns[9], null))
                    .priceInCents(Long.parseLong(csvColumns[18]))
                    .fixedPriceInCents(Long.parseLong(csvColumns[19]))
                    .isCustom(false)
                    .build();
        } catch (NumberFormatException | NullPointerException e) {
            log.warn("Drug " + csvColumns[8] + " couldn't be created du to ", e);
            return null;
        }
    }

    private void createAssociations() {
        Instant start = Instant.now();
        log.info("Creating drug associations");

        atcMap = createATCs();
        dosageFormMap = createDosageForms();
        applicationFormMap = createApplicationForms();
        normPackageSizeMap = createNormPackageSizes();
        producerMap = createProducers();

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        int size = atcMap.size() + dosageFormMap.size() + applicationFormMap.size() + normPackageSizeMap.size()
                + producerMap.size();

        log.info("Created and saved {} associations [{}]", size, duration);
    }

    private Map<String, ATC> createATCs() {
        log.info("Creating ATCs...");
        Instant start = Instant.now();
        String[] csvRows = csvStrings.get(AssociationFile.ATC).split(CSV_ROW_DELIMITER);
        List<ATC> atcs = new ArrayList<>();

        for (String csvRow : csvRows) {
            String[] csvColumns = csvRow.split(CSV_COLUMN_DELIMITER);

            atcs.add(new ATC(csvColumns[2], csvColumns[3]));
        }
        atcRepository.saveAll(atcs);

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        log.info("Created {} ATCs [{}]", atcs.size(), duration);
        return atcs.stream().collect(Collectors.toMap(ATC::getAbbreviation, Function.identity()));
    }

    private Map<String, DosageForm> createDosageForms() {
        log.info("Creating dosage forms...");
        Instant start = Instant.now();
        String[] csvRows = csvStrings.get(AssociationFile.DOSAGE_FORM).split(CSV_ROW_DELIMITER);
        List<DosageForm> dosageForms = new ArrayList<>();

        for (String csvRow : csvRows) {
            String[] csvColumns = csvRow.split(CSV_COLUMN_DELIMITER);

            dosageForms.add(new DosageForm(csvColumns[2], csvColumns[3]));
        }
        dosageFormRepository.saveAll(dosageForms);

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        log.info("Created {} dosage forms [{}]", dosageForms.size(), duration);
        return dosageForms.stream().collect(Collectors.toMap(DosageForm::getAbbreviation, Function.identity()));
    }

    private Map<String, ApplicationForm> createApplicationForms() {
        log.info("Creating application forms...");
        Instant start = Instant.now();
        String[] csvRows = csvStrings.get(AssociationFile.APPLICATION_FORM).split(CSV_ROW_DELIMITER);
        List<ApplicationForm> applicationForms = new ArrayList<>();

        for (String csvRow : csvRows) {
            String[] csvColumns = csvRow.split(CSV_COLUMN_DELIMITER);

            applicationForms.add(new ApplicationForm(csvColumns[2], csvColumns[3]));
        }
        applicationFormRepository.saveAll(applicationForms);

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        log.info("Created {} application forms [{}]", applicationForms.size(), duration);
        return applicationForms.stream()
                .collect(Collectors.toMap(ApplicationForm::getAbbreviation, Function.identity()));
    }

    private Map<String, NormPackageSize> createNormPackageSizes() {
        log.info("Creating norm package sizes...");
        Instant start = Instant.now();
        String[] csvRows = csvStrings.get(AssociationFile.NORM_PACKAGE_SIZE).split(CSV_ROW_DELIMITER);
        List<NormPackageSize> normPackageSizes = new ArrayList<>();

        for (String csvRow : csvRows) {
            String[] csvColumns = csvRow.split(CSV_COLUMN_DELIMITER);

            normPackageSizes.add(new NormPackageSize(csvColumns[2], csvColumns[3]));
        }
        normPackageSizeRepository.saveAll(normPackageSizes);

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        log.info("Created {} norm package sizes [{}]", normPackageSizes.size(), duration);
        return normPackageSizes.stream().collect(Collectors.toMap(NormPackageSize::getId, Function.identity()));
    }

    private Map<String, Producer> createProducers() {
        log.info("Creating producers...");
        Instant start = Instant.now();
        String[] csvRows = csvStrings.get(AssociationFile.PRODUCER).split(CSV_ROW_DELIMITER);
        List<Producer> producers = new ArrayList<>();

        for (String csvRow : csvRows) {
            String[] csvColumns = csvRow.split(CSV_COLUMN_DELIMITER);

            producers.add(new Producer(csvColumns[2], csvColumns[3]));
        }
        producerRepository.saveAll(producers);

        Instant end = Instant.now();
        String duration = DurationFormatUtils.formatDurationHMS(Duration.between(start, end).toMillis());
        log.info("Created {} producers [{}]", producers.size(), duration);
        return producers.stream().collect(Collectors.toMap(Producer::getKey, Function.identity()));
    }
}
