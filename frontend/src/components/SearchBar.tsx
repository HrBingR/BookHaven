// src/components/SearchBar.tsx
import React, { useState } from 'react';
import { Form, FormControl, Button, InputGroup } from 'react-bootstrap';

interface SearchBarProps {
  onSearch: (term: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchTerm);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <InputGroup>
        <div className={"search-bar"}>
          <FormControl
            type="text"
            placeholder="Search for books, authors, or series..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className={"button-spacer"}>
          <Button variant="primary" type="submit">
            Search
          </Button>
        </div>
      </InputGroup>
    </Form>
  );
};

export default SearchBar;