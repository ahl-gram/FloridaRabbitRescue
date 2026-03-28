export default function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/images");
  eleventyConfig.addPassthroughCopy("src/favicon.svg");

  eleventyConfig.addFilter("boardDotClass", function(status) {
    const map = {
      "publicly_listed": "dot-green-s",
      "confirmed_not_listed": "dot-amber-s",
      "sunbiz_principals": "dot-amber-s",
      "not_found": "dot-red-s"
    };
    return map[status] || "dot-amber-s";
  });

  eleventyConfig.addFilter("modelLabel", function(model) {
    const map = {
      "foster_only": "Foster-Based",
      "foster_and_facility": "Foster + Facility"
    };
    return map[model] || model;
  });

  eleventyConfig.addFilter("speciesLabel", function(focus) {
    const map = {
      "rabbits_only": "Rabbits only",
      "rabbits_primary": "Rabbits (primary)",
      "rabbits_and_guinea_pigs": "Rabbits & guinea pigs"
    };
    return map[focus] || focus;
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
