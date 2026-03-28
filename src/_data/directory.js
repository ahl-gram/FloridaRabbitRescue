import { readFileSync } from 'fs';

export default JSON.parse(readFileSync('./directory-data.json', 'utf-8'));
