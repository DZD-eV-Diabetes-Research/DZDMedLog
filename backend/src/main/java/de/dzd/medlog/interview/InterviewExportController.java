package de.dzd.medlog.interview;

import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import java.io.IOException;
import java.time.LocalDate;

@Controller
@RequestMapping("/interview")
@RequiredArgsConstructor
public class InterviewExportController {
    private final InterviewExportService interviewExportService;

    @GetMapping("/export")
    public void exportInterviews(HttpServletResponse response) throws IOException {
        response.setContentType("text/plain; charset=utf-8");
        LocalDate currentDate = LocalDate.now();
        String headerKey = "Content-Disposition";
        String headerValue = "attachment; filename=interviews-" + currentDate + ".csv";
        response.setHeader(headerKey, headerValue);

        String interviewCsv = interviewExportService.getInterviewsAsCsv();

        response.getWriter().print(interviewCsv);
    }
}
