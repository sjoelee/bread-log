--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Homebrew)
-- Dumped by pg_dump version 15.13 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bakers_percentages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bakers_percentages (
    id uuid NOT NULL,
    recipe_id uuid,
    recipe_version_id uuid,
    total_flour_weight numeric(10,2) NOT NULL,
    flour_ingredients jsonb NOT NULL,
    other_ingredients jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: bread_timings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bread_timings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    recipe_name character varying(255) NOT NULL,
    date date DEFAULT CURRENT_DATE,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    autolyse_ts timestamp without time zone,
    mix_ts timestamp without time zone,
    bulk_ts timestamp without time zone,
    preshape_ts timestamp without time zone,
    final_shape_ts timestamp without time zone,
    final_proof_ts timestamp without time zone,
    room_temp numeric(5,1),
    water_temp numeric(5,1),
    flour_temp numeric(5,1),
    preferment_temp numeric(5,1),
    dough_temp numeric(5,1),
    temperature_unit public.temperature_unit_type DEFAULT 'Fahrenheit'::public.temperature_unit_type,
    notes text,
    status character varying(20) DEFAULT 'in_progress'::character varying,
    stretch_fold_count integer DEFAULT 0 NOT NULL,
    bake_ts timestamp without time zone,
    recipe_id uuid,
    recipe_version_id uuid,
    CONSTRAINT bread_timings_status_check CHECK (((status)::text = ANY ((ARRAY['in_progress'::character varying, 'completed'::character varying])::text[])))
);


--
-- Name: recipe_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipe_versions (
    id uuid NOT NULL,
    recipe_id uuid,
    description text,
    ingredients jsonb NOT NULL,
    instructions jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    change_summary jsonb,
    version_number integer NOT NULL
);


--
-- Name: TABLE recipe_versions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.recipe_versions IS 'Recipe versions with simplified version_number field (1, 2, 3, etc.)';


--
-- Name: recipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipes (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    category character varying(100),
    current_version_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    description text
);


--
-- Name: bakers_percentages bakers_percentages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bakers_percentages
    ADD CONSTRAINT bakers_percentages_pkey PRIMARY KEY (id);


--
-- Name: bakers_percentages bakers_percentages_recipe_id_recipe_version_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bakers_percentages
    ADD CONSTRAINT bakers_percentages_recipe_id_recipe_version_id_key UNIQUE (recipe_id, recipe_version_id);


--
-- Name: bread_timings bread_timings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bread_timings
    ADD CONSTRAINT bread_timings_pkey PRIMARY KEY (id);


--
-- Name: recipe_versions recipe_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_versions
    ADD CONSTRAINT recipe_versions_pkey PRIMARY KEY (id);


--
-- Name: recipe_versions recipe_versions_recipe_id_version_number_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_versions
    ADD CONSTRAINT recipe_versions_recipe_id_version_number_unique UNIQUE (recipe_id, version_number);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: idx_bakers_percentages_recipe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bakers_percentages_recipe ON public.bakers_percentages USING btree (recipe_id);


--
-- Name: idx_bakers_percentages_recipe_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bakers_percentages_recipe_version ON public.bakers_percentages USING btree (recipe_version_id);


--
-- Name: idx_bread_timings_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bread_timings_created_at ON public.bread_timings USING btree (created_at);


--
-- Name: idx_bread_timings_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bread_timings_date ON public.bread_timings USING btree (date);


--
-- Name: idx_bread_timings_date_recipe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bread_timings_date_recipe ON public.bread_timings USING btree (date, recipe_name);


--
-- Name: idx_bread_timings_recipe_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bread_timings_recipe_name ON public.bread_timings USING btree (recipe_name);


--
-- Name: idx_bread_timings_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bread_timings_status ON public.bread_timings USING btree (status);


--
-- Name: idx_bread_timings_status_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bread_timings_status_updated_at ON public.bread_timings USING btree (status, updated_at DESC);


--
-- Name: idx_recipe_versions_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_versions_created ON public.recipe_versions USING btree (created_at DESC);


--
-- Name: idx_recipe_versions_ingredients; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_versions_ingredients ON public.recipe_versions USING gin (ingredients);


--
-- Name: idx_recipe_versions_instructions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_versions_instructions ON public.recipe_versions USING gin (instructions);


--
-- Name: idx_recipe_versions_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_versions_recipe_id ON public.recipe_versions USING btree (recipe_id);


--
-- Name: idx_recipe_versions_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_versions_version ON public.recipe_versions USING btree (recipe_id, version_number DESC);


--
-- Name: idx_recipes_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_category ON public.recipes USING btree (category);


--
-- Name: idx_recipes_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_name ON public.recipes USING btree (name);


--
-- Name: idx_recipes_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_updated ON public.recipes USING btree (updated_at DESC);


--
-- Name: bakers_percentages update_bakers_percentages_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_bakers_percentages_updated_at BEFORE UPDATE ON public.bakers_percentages FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: bread_timings update_bread_timings_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_bread_timings_updated_at BEFORE UPDATE ON public.bread_timings FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: recipes update_recipes_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_recipes_updated_at BEFORE UPDATE ON public.recipes FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: bakers_percentages bakers_percentages_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bakers_percentages
    ADD CONSTRAINT bakers_percentages_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: bakers_percentages bakers_percentages_recipe_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bakers_percentages
    ADD CONSTRAINT bakers_percentages_recipe_version_id_fkey FOREIGN KEY (recipe_version_id) REFERENCES public.recipe_versions(id) ON DELETE CASCADE;


--
-- Name: bread_timings bread_timings_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bread_timings
    ADD CONSTRAINT bread_timings_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE SET NULL;


--
-- Name: bread_timings bread_timings_recipe_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bread_timings
    ADD CONSTRAINT bread_timings_recipe_version_id_fkey FOREIGN KEY (recipe_version_id) REFERENCES public.recipe_versions(id) ON DELETE SET NULL;


--
-- Name: recipes fk_recipes_current_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT fk_recipes_current_version FOREIGN KEY (current_version_id) REFERENCES public.recipe_versions(id);


--
-- Name: recipe_versions recipe_versions_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_versions
    ADD CONSTRAINT recipe_versions_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

