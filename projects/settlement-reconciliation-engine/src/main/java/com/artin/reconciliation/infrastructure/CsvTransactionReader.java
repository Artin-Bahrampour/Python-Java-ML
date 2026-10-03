package com.artin.reconciliation.infrastructure;

import com.artin.reconciliation.domain.Transaction;

import java.io.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

public final class CsvTransactionReader {
    private static final List<String> HEADER = List.of("transaction_id", "amount", "currency", "settled_at");

    public List<Transaction> read(Path path) throws IOException {
        if (!Files.isRegularFile(path)) throw new FileNotFoundException(path.toString());
        List<Transaction> result = new ArrayList<>();
        try (BufferedReader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            if (header == null || !parseLine(header).equals(HEADER)) {
                throw new IOException("Invalid CSV header in " + path);
            }
            String line;
            int lineNumber = 1;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                if (line.isBlank()) continue;
                try {
                    List<String> fields = parseLine(line);
                    if (fields.size() != 4) throw new IllegalArgumentException("expected 4 fields");
                    result.add(new Transaction(fields.get(0), new BigDecimal(fields.get(1)), fields.get(2), Instant.parse(fields.get(3))));
                } catch (RuntimeException e) {
                    throw new IOException("Invalid row at " + path + ":" + lineNumber + " (" + e.getMessage() + ")", e);
                }
            }
        }
        return List.copyOf(result);
    }

    static List<String> parseLine(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                if (quoted && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    current.append('"'); i++;
                } else quoted = !quoted;
            } else if (c == ',' && !quoted) {
                fields.add(current.toString().trim()); current.setLength(0);
            } else current.append(c);
        }
        if (quoted) throw new IllegalArgumentException("unterminated quoted field");
        fields.add(current.toString().trim());
        return fields;
    }
}
