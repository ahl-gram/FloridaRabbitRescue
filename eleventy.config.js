export default function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/images");
  eleventyConfig.addPassthroughCopy("src/favicon.svg");

  eleventyConfig.addFilter("modelLabel", function(model) {
    const map = {
      "foster_only": "Foster-Based",
      "foster_and_facility": "Foster + Facility",
      "home_sanctuary": "Home-Based Sanctuary",
      "foster_and_rehabilitation": "Foster + Rehabilitation",
      "sanctuary": "Sanctuary",
      "foster_and_sanctuary": "Foster + Sanctuary",
      "rescue_and_rehome": "Rescue & Rehome",
      "unknown": "Not yet confirmed"
    };
    return map[model] || model;
  });

  eleventyConfig.addFilter("speciesLabel", function(focus) {
    const map = {
      "rabbits_only": "Rabbits only",
      "rabbits_primary": "Rabbits (primary)",
      "rabbits_and_guinea_pigs": "Rabbits & guinea pigs",
      "multi_animal": "Multi-animal rescue",
      "farm_sanctuary": "Farm & animal sanctuary",
      "rabbits_and_small_animals": "Rabbits & small animals",
      "small_animals": "Small animals"
    };
    return map[focus] || focus;
  });

  eleventyConfig.addFilter("sortByName", function(orgs) {
    return [...orgs].sort((a, b) => a.name.localeCompare(b.name));
  });

  eleventyConfig.addFilter("sortByYearsActive", function(orgs) {
    return [...orgs].sort((a, b) => b.years_active - a.years_active);
  });

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data"
    }
  };
}
