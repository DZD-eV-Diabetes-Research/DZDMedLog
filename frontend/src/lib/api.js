// Contains async functions to request internal and external APIs

import config from './config';

/**
 * Example HTTP Request: getPubMedResultsforOrganism
 * 
 * Get PubMed Articles from Neo4J Graph for a gene in a specific organism
 * Requires specific endpoint for given organism
 * API Docs: https://restapi.connect.dzd-ev.de/docs
 * 
 * @param {String} organism 
 * @param {String} gene 
 * @returns Array of article objects
 */
export async function getPubMedResultsforOrganism (organism, gene) {
  const url = config.apiBasePath + 'get' + organism + '/?g=' + gene;
  var results = await (await fetch(url)).json();
  return results;
};
