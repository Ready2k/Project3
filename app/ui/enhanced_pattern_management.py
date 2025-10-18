"""Enhanced Pattern Management UI for Streamlit."""

import streamlit as st
import json
from typing import Any, Dict, Coroutine
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.pattern.enhanced_loader import EnhancedPatternLoader
from app.services.pattern_enhancement_service import PatternEnhancementService
from app.utils.imports import require_service


def run_async_in_thread(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run an async coroutine in a separate thread with its own event loop."""
    def run_in_thread() -> Any:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        except Exception as e:
            # Get logger service for error logging
            app_logger = require_service('logger', context="run_async_in_thread")
            app_logger.error(f"Error running async operation: {e}")
            raise
        finally:
            loop.close()
    
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result(timeout=300)  # 5 minute timeout
    except Exception as e:
        # Get logger service for error logging
        app_logger = require_service('logger', context="run_async_in_thread")
        app_logger.error(f"Failed to run async operation in thread: {e}")
        raise


def render_enhanced_pattern_management(pattern_loader: EnhancedPatternLoader, 
                                     enhancement_service: PatternEnhancementService) -> None:
    """Render the enhanced pattern management interface."""
    
    try:
        st.header("🚀 Enhanced Pattern Management")
        st.markdown("Manage patterns with rich technical details and autonomous agent capabilities")
        
        # Create tabs for different management functions
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Pattern Overview", 
            "🔧 Enhance Patterns", 
            "📋 Pattern Comparison",
            "📈 Pattern Analytics",
            "⚙️ Bulk Operations"
        ])
        
        with tab1:
            render_pattern_overview(pattern_loader)
        
        with tab2:
            render_pattern_enhancement(pattern_loader, enhancement_service)
        
        with tab3:
            render_pattern_comparison(pattern_loader)
        
        with tab4:
            render_pattern_analytics(pattern_loader)
        
        with tab5:
            render_bulk_operations(pattern_loader, enhancement_service)
            
    except Exception as e:
        st.error(f"❌ Error in enhanced pattern management: {e}")
        # Get logger service for error logging
        app_logger = require_service('logger', context="render_enhanced_pattern_management")
        app_logger.error(f"Enhanced pattern management error: {e}")
        
        # Show a helpful message
        st.info("💡 Try refreshing the page or check the application logs for more details.")
        
        # Show debug info in expander
        with st.expander("Debug Information"):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())


def render_pattern_overview(pattern_loader: EnhancedPatternLoader) -> None:
    """Render pattern overview with enhanced capabilities."""
    
    st.subheader("Pattern Library Overview")
    
    try:
        # Get pattern statistics
        stats = pattern_loader.get_pattern_statistics()
    except Exception as e:
        st.error(f"❌ Failed to load pattern statistics: {e}")
        # Get logger service for error logging
        app_logger = require_service('logger', context="render_pattern_overview")
        app_logger.error(f"Pattern statistics error: {e}")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patterns", stats["total_patterns"])
    
    with col2:
        agentic_count = stats["capabilities"].get("has_agentic_features", 0)
        st.metric("Agentic Patterns", agentic_count)
    
    with col3:
        enhanced_count = stats["capabilities"].get("has_detailed_tech_stack", 0)
        st.metric("Enhanced Tech Stack", enhanced_count)
    
    with col4:
        guidance_count = stats["capabilities"].get("has_implementation_guidance", 0)
        st.metric("Implementation Guidance", guidance_count)
    
    # Pattern type distribution
    st.subheader("Pattern Type Distribution")
    type_data = stats["by_type"]
    if type_data:
        st.bar_chart(type_data)
    
    # Capability matrix
    st.subheader("Pattern Capabilities Matrix")
    
    patterns = pattern_loader.load_patterns()
    if patterns:
        capability_data = []
        
        for pattern in patterns[:20]:  # Limit to first 20 for display
            capabilities = pattern.get("_capabilities", {})
            capability_data.append({
                "Pattern ID": pattern.get("pattern_id", "Unknown"),
                "Name": pattern.get("name", "Unknown")[:30] + "..." if len(pattern.get("name", "")) > 30 else pattern.get("name", "Unknown"),
                "Agentic": "✅" if capabilities.get("has_agentic_features") else "❌",
                "Tech Stack": "✅" if capabilities.get("has_detailed_tech_stack") else "❌",
                "Guidance": "✅" if capabilities.get("has_implementation_guidance") else "❌",
                "Effort Detail": "✅" if capabilities.get("has_detailed_effort_breakdown") else "❌",
                "Complexity": pattern.get("_complexity_score", 0.5)
            })
        
        st.dataframe(capability_data, use_container_width=True)


def render_pattern_enhancement(pattern_loader: EnhancedPatternLoader, 
                             enhancement_service: PatternEnhancementService) -> None:
    """Render pattern enhancement interface."""
    
    st.subheader("Pattern Enhancement")
    
    try:
        # Get enhancement candidates
        candidates = enhancement_service.get_enhancement_candidates()
    except Exception as e:
        st.error(f"❌ Failed to get enhancement candidates: {e}")
        # Get logger service for error logging
        app_logger = require_service('logger', context="render_pattern_enhancement")
        app_logger.error(f"Enhancement candidates error: {e}")
        return
    
    if not candidates:
        st.info("All patterns are already enhanced! 🎉")
        return
    
    st.markdown(f"Found **{len(candidates)}** patterns that could benefit from enhancement:")
    
    # Enhancement type selection
    enhancement_type = st.selectbox(
        "Enhancement Type",
        ["full", "technical", "agentic"],
        help="Full: Both technical details and agentic capabilities, Technical: Implementation details only, Agentic: Autonomous capabilities only"
    )
    
    # Show enhancement type description
    if enhancement_type == "agentic":
        st.info("🤖 **Agentic Enhancement**: Will add autonomous agent capabilities, decision-making logic, and self-monitoring features to patterns.")
    elif enhancement_type == "technical":
        st.info("⚙️ **Technical Enhancement**: Will add detailed implementation guidance, code examples, and technical specifications.")
    elif enhancement_type == "full":
        st.info("🚀 **Full Enhancement**: Will add both technical implementation details and autonomous agent capabilities.")
    
    # Filter candidates based on enhancement type if needed
    filtered_candidates = candidates
    if enhancement_type == "agentic":
        # Prioritize patterns that would benefit most from agentic capabilities
        filtered_candidates = [c for c in candidates if 
                             c.get('complexity', 'low') in ['medium', 'high'] or
                             'agentic' in str(c.get('missing_capabilities', [])).lower()]
    elif enhancement_type == "technical":
        # Prioritize patterns missing technical details
        filtered_candidates = [c for c in candidates if 
                             'technical' in str(c.get('missing_capabilities', [])).lower() or
                             not c.get('has_implementation_details', False)]
    
    # Pattern selection for enhancement
    selected_patterns = []
    
    # Show filtered results count
    if len(filtered_candidates) != len(candidates):
        st.success(f"🎯 Filtered to {len(filtered_candidates)} patterns most suitable for {enhancement_type} enhancement")
    
    with st.expander("Select Patterns to Enhance", expanded=True):
        display_candidates = filtered_candidates[:10]  # Show top 10 filtered candidates
        
        if not display_candidates:
            st.warning(f"No patterns found that would benefit from {enhancement_type} enhancement.")
            return
            
        for candidate in display_candidates:
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            
            with col1:
                selected = st.checkbox(
                    f"Select {candidate['pattern_id']}", 
                    key=f"enhance_{candidate['pattern_id']}",
                    label_visibility="collapsed"
                )
                if selected:
                    selected_patterns.append(candidate['pattern_id'])
            
            with col2:
                st.write(f"**{candidate['pattern_id']}**")
                st.write(candidate['name'][:50] + "..." if len(candidate['name']) > 50 else candidate['name'])
            
            with col3:
                st.write(f"Complexity: {candidate['complexity']}")
                st.write(f"Potential: {candidate['enhancement_potential']:.2f}")
            
            with col4:
                missing = candidate.get('missing_capabilities', [])
                if missing:
                    st.write("Missing:")
                    for cap in missing[:2]:  # Show first 2
                        st.write(f"• {cap.replace('has_', '').replace('_', ' ').title()}")
                
                # Show what this enhancement type will add
                if enhancement_type == "agentic":
                    st.write("🤖 Will add: Agent logic")
                elif enhancement_type == "technical":
                    st.write("⚙️ Will add: Tech details")
                elif enhancement_type == "full":
                    st.write("🚀 Will add: Both")
    
    # Enhancement action
    if selected_patterns:
        st.markdown(f"**Selected {len(selected_patterns)} patterns for enhancement**")
        
        if st.button("🚀 Enhance Selected Patterns", type="primary"):
            with st.spinner("Enhancing patterns... This may take a few minutes."):
                try:
                    # Run enhancement in separate thread to avoid event loop conflicts
                    results = run_async_in_thread(
                        enhancement_service.batch_enhance_patterns(selected_patterns, enhancement_type)
                    )
                    
                    # Display results
                    if results["successful"]:
                        st.success(f"✅ Successfully enhanced {len(results['successful'])} patterns!")
                        
                        for result in results["successful"]:
                            st.write(f"• {result['original_id']} → {result['enhanced_id']}")
                    
                    if results["failed"]:
                        st.error(f"❌ Failed to enhance {len(results['failed'])} patterns:")
                        
                        for result in results["failed"]:
                            st.write(f"• {result['pattern_id']}: {result['error']}")
                    
                    # Refresh pattern cache
                    pattern_loader.refresh_cache()
                    try:
                        st.rerun()
                    except AttributeError:
                        # Fallback for older Streamlit versions
                        st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"❌ Enhancement failed: {e}")
                    # Get logger service for error logging
                    app_logger = require_service('logger', context="render_pattern_enhancement")
                    app_logger.error(f"Pattern enhancement error: {e}")
                    
                    with st.expander("Error Details"):
                        st.code(str(e))
                        import traceback
                        st.code(traceback.format_exc())


def render_pattern_comparison(pattern_loader: EnhancedPatternLoader) -> None:
    """Render pattern comparison interface."""
    
    st.subheader("Pattern Comparison")
    
    patterns = pattern_loader.load_patterns()
    pattern_options = {f"{p.get('pattern_id', 'Unknown')} - {p.get('name', 'Unknown')}": p.get('pattern_id', 'Unknown') 
                      for p in patterns}
    
    col1, col2 = st.columns(2)
    
    with col1:
        pattern1_key = st.selectbox("Select First Pattern", list(pattern_options.keys()))
        pattern1_id = pattern_options[pattern1_key] if pattern1_key else None
    
    with col2:
        pattern2_key = st.selectbox("Select Second Pattern", list(pattern_options.keys()))
        pattern2_id = pattern_options[pattern2_key] if pattern2_key else None
    
    if pattern1_id and pattern2_id and pattern1_id != pattern2_id:
        pattern1 = pattern_loader.get_pattern_by_id(pattern1_id)
        pattern2 = pattern_loader.get_pattern_by_id(pattern2_id)
        
        if pattern1 and pattern2:
            render_pattern_comparison_details(pattern1, pattern2)


def render_pattern_comparison_details(pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> None:
    """Render detailed comparison between two patterns."""
    
    st.subheader("Detailed Comparison")
    
    # Basic comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {pattern1.get('pattern_id', 'Unknown')}")
        st.write(f"**Name:** {pattern1.get('name', 'Unknown')}")
        st.write(f"**Feasibility:** {pattern1.get('feasibility', 'Unknown')}")
        st.write(f"**Complexity:** {pattern1.get('complexity', 'Unknown')}")
        st.write(f"**Domain:** {pattern1.get('domain', 'Unknown')}")
        
        if pattern1.get('autonomy_level'):
            st.write(f"**Autonomy Level:** {pattern1.get('autonomy_level', 0):.2f}")
    
    with col2:
        st.markdown(f"### {pattern2.get('pattern_id', 'Unknown')}")
        st.write(f"**Name:** {pattern2.get('name', 'Unknown')}")
        st.write(f"**Feasibility:** {pattern2.get('feasibility', 'Unknown')}")
        st.write(f"**Complexity:** {pattern2.get('complexity', 'Unknown')}")
        st.write(f"**Domain:** {pattern2.get('domain', 'Unknown')}")
        
        if pattern2.get('autonomy_level'):
            st.write(f"**Autonomy Level:** {pattern2.get('autonomy_level', 0):.2f}")
    
    # Tech stack comparison
    st.subheader("Technology Stack Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Pattern 1 Tech Stack")
        tech_stack1 = pattern1.get('tech_stack', [])
        if isinstance(tech_stack1, dict):
            for category, technologies in tech_stack1.items():
                st.write(f"**{category.replace('_', ' ').title()}:**")
                for tech in technologies:
                    st.write(f"• {tech}")
        else:
            for tech in tech_stack1:
                st.write(f"• {tech}")
    
    with col2:
        st.markdown("#### Pattern 2 Tech Stack")
        tech_stack2 = pattern2.get('tech_stack', [])
        if isinstance(tech_stack2, dict):
            for category, technologies in tech_stack2.items():
                st.write(f"**{category.replace('_', ' ').title()}:**")
                for tech in technologies:
                    st.write(f"• {tech}")
        else:
            for tech in tech_stack2:
                st.write(f"• {tech}")
    
    # Capabilities comparison
    st.subheader("Capabilities Comparison")
    
    capabilities1 = pattern1.get('_capabilities', {})
    capabilities2 = pattern2.get('_capabilities', {})
    
    comparison_data = []
    for capability in capabilities1.keys():
        comparison_data.append({
            "Capability": capability.replace('has_', '').replace('_', ' ').title(),
            "Pattern 1": "✅" if capabilities1.get(capability) else "❌",
            "Pattern 2": "✅" if capabilities2.get(capability) else "❌"
        })
    
    st.dataframe(comparison_data, use_container_width=True)


def render_pattern_analytics(pattern_loader: EnhancedPatternLoader) -> None:
    """Render pattern analytics and insights."""
    
    st.subheader("Pattern Analytics")
    
    patterns = pattern_loader.load_patterns()
    pattern_loader.get_pattern_statistics()
    
    # Complexity distribution
    st.subheader("Complexity Score Distribution")
    
    complexity_scores = [p.get('_complexity_score', 0.5) for p in patterns]
    if complexity_scores:
        try:
            import numpy as np
            import pandas as pd
            
            # Create histogram data
            hist, bin_edges = np.histogram(complexity_scores, bins=20)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Create DataFrame for chart
            hist_df = pd.DataFrame({
                'Complexity Score': [f"{edge:.2f}" for edge in bin_centers],
                'Count': hist
            }).set_index('Complexity Score')
            
            st.bar_chart(hist_df)
        except ImportError as e:
            st.error(f"❌ Missing required packages for histogram: {e}")
            st.info("💡 Install numpy and pandas to view complexity distribution")
    else:
        st.info("No complexity scores available")
    
    # Autonomy level distribution (for agentic patterns)
    agentic_patterns = [p for p in patterns if p.get('autonomy_level')]
    
    if agentic_patterns:
        st.subheader("Autonomy Level Distribution")
        autonomy_scores = [p.get('autonomy_level', 0) for p in agentic_patterns]
        
        if autonomy_scores:
            try:
                import numpy as np
                import pandas as pd
                
                # Create histogram data
                hist, bin_edges = np.histogram(autonomy_scores, bins=10)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                
                # Create DataFrame for chart
                hist_df = pd.DataFrame({
                    'Autonomy Level': [f"{edge:.2f}" for edge in bin_centers],
                    'Count': hist
                }).set_index('Autonomy Level')
                
                st.bar_chart(hist_df)
            except ImportError as e:
                st.error(f"❌ Missing required packages for histogram: {e}")
                st.info("💡 Install numpy and pandas to view autonomy distribution")
        else:
            st.info("No autonomy scores available")
    
    # Technology usage analysis
    st.subheader("Technology Usage Analysis")
    
    tech_usage = {}
    for pattern in patterns:
        tech_stack = pattern.get('tech_stack', [])
        if isinstance(tech_stack, list):
            for tech in tech_stack:
                tech_usage[tech] = tech_usage.get(tech, 0) + 1
        elif isinstance(tech_stack, dict):
            for category, technologies in tech_stack.items():
                for tech in technologies:
                    tech_usage[tech] = tech_usage.get(tech, 0) + 1
    
    # Show top 20 technologies
    sorted_tech = sorted(tech_usage.items(), key=lambda x: x[1], reverse=True)[:20]
    
    if sorted_tech:
        tech_chart_data = {tech: count for tech, count in sorted_tech}
        st.bar_chart(tech_chart_data)
    
    # Pattern type analysis
    st.subheader("Pattern Type Analysis")
    
    pattern_type_usage = {}
    for pattern in patterns:
        pattern_types = pattern.get('pattern_type', [])
        for ptype in pattern_types:
            pattern_type_usage[ptype] = pattern_type_usage.get(ptype, 0) + 1
    
    if pattern_type_usage:
        st.bar_chart(pattern_type_usage)


def render_bulk_operations(pattern_loader: EnhancedPatternLoader, 
                          enhancement_service: PatternEnhancementService) -> None:
    """Render bulk operations interface."""
    
    st.subheader("Bulk Operations")
    
    patterns = pattern_loader.load_patterns()
    
    # Bulk enhancement
    st.markdown("### Bulk Enhancement")
    
    enhancement_type = st.selectbox(
        "Enhancement Type for Bulk Operation",
        ["full", "technical", "agentic"],
        key="bulk_enhancement_type"
    )
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        complexity_filter = st.multiselect(
            "Filter by Complexity",
            ["Low", "Medium", "High", "Very High"],
            default=["Medium", "High"]
        )
    
    with col2:
        pattern_type_filter = st.multiselect(
            "Filter by Pattern Type",
            ["traditional", "agentic", "enhanced"],
            default=["traditional"]
        )
    
    # Get filtered patterns
    filtered_patterns = []
    for pattern in patterns:
        if (pattern.get('complexity') in complexity_filter and 
            pattern.get('_pattern_type') in pattern_type_filter):
            filtered_patterns.append(pattern)
    
    st.write(f"Found {len(filtered_patterns)} patterns matching filters")
    
    if filtered_patterns and st.button("🚀 Enhance All Filtered Patterns", type="primary"):
        pattern_ids = [p.get('pattern_id') for p in filtered_patterns]
        
        with st.spinner(f"Enhancing {len(pattern_ids)} patterns... This may take several minutes."):
            try:
                results = run_async_in_thread(
                    enhancement_service.batch_enhance_patterns(pattern_ids, enhancement_type)
                )
                
                st.success("Bulk enhancement completed!")
                st.write(f"✅ Successful: {len(results['successful'])}")
                st.write(f"❌ Failed: {len(results['failed'])}")
                
                if results['failed']:
                    with st.expander("View Failed Enhancements"):
                        for failure in results['failed']:
                            st.write(f"• {failure['pattern_id']}: {failure['error']}")
                
                pattern_loader.refresh_cache()
                try:
                    st.rerun()
                except AttributeError:
                    # Fallback for older Streamlit versions
                    st.experimental_rerun()  # type: ignore  # type: ignore
                
            except Exception as e:
                st.error(f"❌ Bulk enhancement failed: {e}")
                # Get logger service for error logging
                app_logger = require_service('logger', context="render_bulk_operations")
                app_logger.error(f"Bulk pattern enhancement error: {e}")
                
                with st.expander("Error Details"):
                    st.code(str(e))
                    import traceback
                    st.code(traceback.format_exc())
    
    # Export operations
    st.markdown("### Export Operations")
    
    export_format = st.selectbox(
        "Export Format",
        ["JSON", "CSV", "Markdown"]
    )
    
    if st.button("📥 Export All Patterns"):
        if export_format == "JSON":
            export_data = json.dumps(patterns, indent=2)
            st.download_button(
                "Download JSON",
                export_data,
                "enhanced_patterns.json",
                "application/json"
            )
        elif export_format == "CSV":
            # Convert to CSV format
            import pandas as pd
            
            csv_data = []
            for pattern in patterns:
                csv_data.append({
                    "pattern_id": pattern.get('pattern_id'),
                    "name": pattern.get('name'),
                    "feasibility": pattern.get('feasibility'),
                    "complexity": pattern.get('complexity'),
                    "domain": pattern.get('domain'),
                    "autonomy_level": pattern.get('autonomy_level', ''),
                    "pattern_type": pattern.get('_pattern_type', ''),
                    "complexity_score": pattern.get('_complexity_score', '')
                })
            
            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)
            
            st.download_button(
                "Download CSV",
                csv_string,
                "enhanced_patterns.csv",
                "text/csv"
            )
        elif export_format == "Markdown":
            # Generate markdown report
            md_content = "# Enhanced Pattern Library Report\n\n"
            
            stats = pattern_loader.get_pattern_statistics()
            md_content += f"**Total Patterns:** {stats['total_patterns']}\n\n"
            
            for pattern in patterns:
                md_content += f"## {pattern.get('pattern_id')} - {pattern.get('name')}\n\n"
                md_content += f"**Feasibility:** {pattern.get('feasibility')}\n"
                md_content += f"**Complexity:** {pattern.get('complexity')}\n"
                md_content += f"**Domain:** {pattern.get('domain')}\n\n"
                md_content += f"{pattern.get('description', '')}\n\n"
                md_content += "---\n\n"
            
            st.download_button(
                "Download Markdown",
                md_content,
                "enhanced_patterns.md",
                "text/markdown"
            )