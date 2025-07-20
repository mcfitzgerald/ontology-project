# ADK Manufacturing Analytics System - Improvement Plan

Based on session analysis and feedback, this document outlines the recommended improvements for the ADK Manufacturing Analytics System.

## 1. Enhance Agent Prompting & Create Evaluation Framework

### Objectives
- Enforce discovery-first approach in agent behavior
- Enable proactive query execution
- Create measurable evaluation metrics

### Sub-tasks
- [ ] Update agent system prompts to enforce discovery-first approach
- [ ] Add explicit instructions for proactive query execution
- [ ] Create evaluation framework using proven patterns:
  - [ ] Build test suite based on $2.5M optimization case studies
  - [ ] Implement metrics for discovery-first compliance rate
  - [ ] Score proactive execution behavior
  - [ ] Track successful query pattern usage

### Success Criteria
- Agents always discover entities before complex queries
- No more "Should I execute this query?" prompts
- Evaluation scores > 90% on proven patterns

## 2. Add Generic Python Execution Environment

### Objectives
- Enable flexible, LLM-generated Python analysis
- Support exploratory data analysis without rigid templates
- Maintain safety and resource boundaries

### Sub-tasks
- [ ] Implement Python execution capability with:
  - [ ] Pandas DataFrame support (leveraging API's DataFrame-compatible format)
  - [ ] Numpy and basic scientific libraries
  - [ ] Matplotlib/seaborn for visualizations
- [ ] Add safety features:
  - [ ] Execution timeouts
  - [ ] Memory limits
  - [ ] Import restrictions (whitelist approach)
- [ ] Enable napkin-style calculations with user input
- [ ] Support ad-hoc visualizations

### Success Criteria
- LLM can generate and execute custom Python analysis
- Safety boundaries prevent resource exhaustion
- Seamless integration with SPARQL query results

## 3. Smart Visualization Guidance (Not Templates)

### Objectives
- Provide principles for visualization without rigid templates
- Let Python environment handle flexible chart creation

### Sub-tasks
- [ ] Add general guidance on when to suggest visualizations
- [ ] Remove any template-based visualization constraints
- [ ] Let Python environment be the primary visualization tool

### Success Criteria
- Agents suggest visualizations contextually
- No prescriptive chart types limiting creativity

## 4. Enhance Context Loading with Non-Redundant Examples

### Objectives
- Use cached successful queries as both context and evaluation data
- Include proven case studies without redundancy

### Sub-tasks
- [ ] Add successful query patterns from cache as context
- [ ] Include $2.5M case studies as examples
- [ ] Add entity validation queries only where they complement existing resources
- [ ] Ensure no redundancy with mindmap TTL and data catalogue

### Success Criteria
- Context provides valuable examples without duplication
- Case studies serve as both guidance and evaluation benchmarks

## 5. Flexible Financial Analysis Framework

### Objectives
- Enable conversational financial analysis
- Avoid rigid calculators or predetermined patterns

### Sub-tasks
- [ ] Add conversational prompts for financial analysis:
  - [ ] Guide napkin-style calculations
  - [ ] Prompt for user inputs on costs/benefits
  - [ ] Support iterative refinement
- [ ] Use Python environment for custom financial modeling
- [ ] Remove focus on "opportunities" - emphasize exploration

### Success Criteria
- Financial analysis feels conversational and flexible
- No rigid ROI calculators limiting analysis
- Users can explore financial impacts naturally

## 6. Improve User Experience

### Objectives
- Reduce friction in the analysis flow
- Provide better feedback and error handling

### Sub-tasks
- [ ] Remove unnecessary confirmation prompts
- [ ] Add progress indicators for multi-step analyses
- [ ] Implement better error messages with recovery suggestions
- [ ] Improve response formatting for clarity

### Success Criteria
- Smoother user experience with less back-and-forth
- Clear progress tracking for complex analyses
- Helpful error messages that guide recovery

## 7. Technical Improvements

### Objectives
- Better handle edge cases and failures
- Improve query generation and caching

### Sub-tasks
- [ ] Enhance SPARQL tool's aggregation failure handling
- [ ] Improve automatic query rewriting for common patterns
- [ ] Better integration between cached results and Python analysis
- [ ] Simplify financial calculation formatting

### Success Criteria
- Fewer query failures due to aggregation issues
- Seamless data flow between SPARQL and Python
- Clean, simple output formatting

## Implementation Priority

1. **High Priority** (Week 1)
   - Python execution environment (enables many other improvements)
   - Remove confirmation prompts (quick UX win)
   - Basic evaluation framework

2. **Medium Priority** (Week 2)
   - Enhanced prompting for discovery-first and proactive execution
   - Context loading improvements
   - Technical query handling improvements

3. **Lower Priority** (Week 3+)
   - Refined financial analysis framework
   - Advanced evaluation metrics
   - Additional UX improvements

## Evaluation Metrics

- Discovery-first compliance: % of analyses starting with entity discovery
- Proactive execution rate: % of queries executed without confirmation
- Case study alignment: Score against known successful patterns
- User satisfaction: Time to insight, number of iterations required
- Technical reliability: Query success rate, error recovery rate