package de.dzd.idom.interview;

import de.dzd.idom.drug.Drug;
import de.dzd.idom.drug.DrugRepository;
import de.dzd.idom.intake.Intake;
import de.dzd.idom.intake.IntakeDTO;
import de.dzd.idom.interview.event.Event;
import de.dzd.idom.interview.event.EventRepository;
import lombok.extern.slf4j.Slf4j;
import org.modelmapper.ModelMapper;
import org.modelmapper.PropertyMap;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Slf4j
@Component
public class InterviewMapper {
    private final DrugRepository drugRepository;
    private final EventRepository eventRepository;
    private final ModelMapper mapper;

    @Autowired
    public InterviewMapper(DrugRepository drugRepository, EventRepository eventRepository) {
        this.drugRepository = drugRepository;
        this.eventRepository = eventRepository;
        mapper = new ModelMapper();
        mapper.getConfiguration().setSkipNullEnabled(true);
        mapper.addMappings(new PropertyMap<InterviewDTO, Interview>() {
            @Override
            protected void configure() {
                skip(destination.getId());
                skip(destination.getEvent());
            }
        });
        mapper.addMappings(new PropertyMap<IntakeDTO, Intake>() {
            @Override
            protected void configure() {
                skip(destination.getId());
                skip(destination.getDrug());
                map().setIsPrescribed(source.isPrescribed());
                map().setIsRegularly(source.isRegularly());
                map().setIsTakenToday(source.isTakenToday());
            }
        });
    }
    public Interview convertToEntity(InterviewDTO interviewDTO) {
        Interview interview = mapper.map(interviewDTO, Interview.class);
        Optional<Event> eventOptional = eventRepository.findById(interviewDTO.getEventId());
        interview.setEvent(eventOptional.orElse(new Event(interviewDTO.getEventId())));

        // fetch correct drug entity and set interview in every intake
        for (int i = 0; i < interviewDTO.getIntakes().size(); i++) {
            IntakeDTO intakeDTO = interviewDTO.getIntakes().get(i);
            Optional<Drug> persistedDrug = drugRepository.findById(intakeDTO.getDrugId());
            interview.getIntakes().get(i).setDrug(persistedDrug.get());
            interview.getIntakes().get(i).setInterview(interview);
        }
        return interview;
    }
}
