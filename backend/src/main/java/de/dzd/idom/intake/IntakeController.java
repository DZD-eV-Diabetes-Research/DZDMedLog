package de.dzd.idom.intake;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/intake")
@AllArgsConstructor
public class IntakeController {
    private IntakeRepository intakeRepository;

    @RequestMapping("/all")
    public List<Intake> getAllIntakes() {
        return intakeRepository.findAll();
    }
}
