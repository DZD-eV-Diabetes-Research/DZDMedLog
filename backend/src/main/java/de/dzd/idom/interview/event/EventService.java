package de.dzd.idom.interview.event;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class EventService {
    private final EventRepository eventRepository;

    public List<Event> findAll() {
        return eventRepository.findAll();
    }
    public Optional<Event> findById(Long id) {
        return eventRepository.findById(id);
    }
    public Event save(Event event) {
        return eventRepository.save(event);
    }
}
