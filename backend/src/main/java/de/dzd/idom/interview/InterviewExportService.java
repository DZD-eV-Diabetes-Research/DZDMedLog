package de.dzd.idom.interview;

import de.dzd.idom.intake.Intake;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Iterator;
import java.util.List;

@Service
@RequiredArgsConstructor
public class InterviewExportService {
    private final InterviewRepository interviewRepository;

    public String getInterviewsAsCsv() {
        List<Interview> interviews = interviewRepository.findAll();
        StringBuilder interviewCsv = new StringBuilder("ID;ProbantID;EventID;InterviewNr;Startdate;Enddate;HasTakenOtherDrugs;DrugNr,DrugName,ATC,Dose,IsPrescribed,IsRegularIntake,IntakeStartDate,IntakeEndDate,DosesPerDay,IntakeInterval,IsTakenToday\n");

        interviews.forEach(interview -> {
            interviewCsv.append(interview.getId()).append(";")
                    .append(interview.getProbandId()).append(";")
                    .append(interview.getEvent().getId()).append(";")
                    .append(interview.getInterviewNumber()).append(";")
                    .append(interview.getStartDate()).append(";")
                    .append(interview.getEndDate()).append(";")
                    .append(interview.getHasTakenOtherDrugs() ? 1 : 0).append(";");

            for (Iterator<Intake> intakeIterator = interview.getIntakes().iterator(); intakeIterator.hasNext();) {
                Intake intake = intakeIterator.next();

                interviewCsv.append(intake.getDrug().getPharmaceuticalCentralNumber()).append(",")
                    .append(intake.getDrug().getName()).append(",")
                    .append(intake.getDrug().getAtc().getAbbreviation()).append(",")
                    .append(intake.getDrug().getPackageSize()).append(intake.getDoseUnit()).append(",")
                    .append(intake.getIsPrescribed() ? 1 : 0).append(",")
                    .append(intake.getIsRegularly() ? 1 : 0).append(",")
                    .append(intake.getStartDate()).append(",")
                    .append(intake.getEndDate()).append(",")
                    .append(intake.getDosePerDay()).append(",")
                    .append(intake.getIntakeInterval()).append(",")
                    .append(intake.getIsTakenToday() ? 1 : 0);

                if (intakeIterator.hasNext()) {
                    interviewCsv.append("|");
                }
            }
            interviewCsv.append("\n");
        });
        return interviewCsv.toString();
    }
}
